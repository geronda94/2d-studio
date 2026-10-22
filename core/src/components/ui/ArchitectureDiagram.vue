<script setup lang="ts">
import {
  ref,
  computed,
  onMounted,
  onUnmounted,
  nextTick,
  watch,
  inject,
} from "vue";
import { Icon } from "@iconify/vue";
import { useVariant } from "../../composables/useVariant";
import { getHexColor, getColorAlpha } from "../../utils/colors";

const props = defineProps<{
  nodes?: any[];
  showDataFlow?: boolean;
  show_data_flow?: boolean;
  mobile?: boolean;
  variant?: string;
}>();

const { itemVars, itemPrimaryVars, line } = useVariant(
  computed(() => props.variant),
  "ArchitectureDiagram",
);

// Общий стиль ноды из варианта (форма/материал); семантические цвета остаются в компоненте.
// Значения берутся через CSS-переменные, поэтому реактивность обеспечивает itemVars/itemPrimaryVars на корне.
function nodeStyleFor(prefix) {
  return {
    background: `var(--${prefix}-bg)`,
    backdropFilter: `var(--${prefix}-backdrop)`,
    WebkitBackdropFilter: `var(--${prefix}-backdrop)`,
    borderRadius: `var(--${prefix}-radius)`,
    boxShadow: `var(--${prefix}-shadow)`,
    padding: `var(--${prefix}-padding)`,
    gap: `var(--${prefix}-gap)`,
    borderWidth: `var(--${prefix}-border-width)`,
    borderStyle: `var(--${prefix}-border-style)`,
  };
}
const nodeStyle = nodeStyleFor("item");
const nodePrimaryStyle = nodeStyleFor("item-primary");

const relativeTime = inject<any>("relativeTime", ref(0));
const isHeadlessRender = computed(
  () =>
    typeof window !== "undefined" &&
    !!window.navigator &&
    (window.navigator.webdriver ||
      new URLSearchParams(window.location.search).get("render") === "true"),
);
const shouldAnimateFlow = computed(
  () => dataFlowEnabled.value && !isHeadlessRender.value,
);

// Приоритет анимации потока: вариант 'none' = статично всегда;
// явное поле связи animation — выше варианта; иначе — вариант.
const flowAnimation = (path: any) => {
  const v = line.value?.animation ?? "dash";
  if (v === "none") return "none";
  return path.animation || v;
};

// --- Auto-layout logic (Adapted from InteractiveArchitecture) ---
const processedData = computed(() => {
  const rawNodes = Array.isArray(props.nodes) ? props.nodes : [];
  const nodeMap = new Map<string, any>();
  const inDegree = new Map<string, number>();
  const layers = new Map<string, number>();

  const normalizedNodes = rawNodes.map((n: any) => {
    const node = { ...n };
    if (node.type === "core" && node.is_main === undefined) {
      node.is_main = true;
      delete node.type;
    }
    return node;
  });

  const uniqueNodes: any[] = [];
  normalizedNodes.forEach((n: any) => {
    if (!nodeMap.has(n.id)) {
      nodeMap.set(n.id, n);
      inDegree.set(n.id, 0);
      layers.set(n.id, 0);
      uniqueNodes.push(n);
    }
  });

  const edges: any[] = [];
  uniqueNodes.forEach((n: any) => {
    if (n.to && Array.isArray(n.to)) {
      n.to.forEach((t: any) => {
        const targetId = typeof t === "string" ? t : t.id;
        const targetNode = nodeMap.get(targetId);

        if (!targetNode) return;

        const sourceTime = n.start_time ?? 0;
        const targetTime = targetNode.start_time ?? 0;
        const drawDuration = 500;

        let edgeTime = targetTime - drawDuration;
        let edgeTargetTime = targetTime;

        if (edgeTime < sourceTime) {
          edgeTime = sourceTime;
          edgeTargetTime = sourceTime + drawDuration;
        }

        if (typeof t === "object" && t.start_time !== undefined) {
          edgeTime = t.start_time;
          edgeTargetTime = edgeTime + drawDuration;
        }

        const flowColor = getHexColor(n.color);
        // Явная анимация связи из данных (to: {id, animation}) — приоритет над
        // вариантом; null = «как скажет вариант». Дефолт 'dash' не ставим,
        // иначе строковые to заглушат particles/pulse варианта.
        const animation =
          typeof t === "object" ? t.animation || null : null;
        const targetIdStr = typeof t === "string" ? t : t.id;

        edges.push({
          from: n.id,
          to: targetIdStr,
          color: flowColor,
          animation,
          start_time: edgeTime,
          target_time: edgeTargetTime,
        });
      });
    }
  });

  edges.forEach((e) => {
    if (inDegree.has(e.to)) {
      inDegree.set(e.to, inDegree.get(e.to)! + 1);
    }
  });

  const queue = uniqueNodes
    .filter((n: any) => inDegree.get(n.id) === 0)
    .map((n: any) => n.id);

  while (queue.length > 0) {
    const currentId = queue.shift()!;
    const currentLayer = layers.get(currentId)!;

    const outgoing = edges.filter((e) => e.from === currentId);
    outgoing.forEach((e) => {
      const nextLayer = Math.max(layers.get(e.to)!, currentLayer + 1);
      layers.set(e.to, nextLayer);
      const indeg = inDegree.get(e.to)! - 1;
      inDegree.set(e.to, indeg);
      if (indeg === 0) queue.push(e.to);
    });
  }

  const layerGroups = new Map<number, string[]>();
  layers.forEach((layer, id) => {
    if (!layerGroups.has(layer)) layerGroups.set(layer, []);
    layerGroups.get(layer)!.push(id);
  });

  const colSpacing = props.mobile ? 200 : 300;
  const rowSpacing = props.mobile ? 140 : 160;
  const maxLayer = Math.max(...Array.from(layerGroups.keys()), 0);
  const centerCol = maxLayer / 2;
  let minX = 0;
  let maxX = 0;
  let minY = 0;
  let maxY = 0;

  const layoutNodes = uniqueNodes.map((node: any) => {
    const layer = layers.get(node.id) ?? 0;
    const layerSize = (layerGroups.get(layer) || []).length;
    const layerIndex = indexOf(node.id, layerGroups.get(layer) || []);
    let x = 0;
    let y = 0;

    if (props.mobile) {
      // Вертикальный поток (как до рефакторинга): слои сверху вниз,
      // ноды слоя — в ряд по горизонтали. На узкой сцене иначе не читается.
      let currentColSpacing = colSpacing * 0.95;
      if (layerSize >= 3) {
        currentColSpacing = 90;
      }
      x = (layerIndex - (layerSize - 1) / 2) * currentColSpacing;
      y = (layer - centerCol) * rowSpacing;
      // Шахматка для слоёв из 3+ нод
      if (layerSize >= 3 && layerIndex % 2 !== 0) {
        y += 100;
      }
    } else {
      x = (layer - centerCol) * colSpacing;
      y =
        (indexOf(node.id, layerGroups.get(layer) || []) - (layerSize - 1) / 2) *
        rowSpacing;
    }

    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);

    // Момент появления: когда дорисована САМАЯ ПОЗДНЯЯ входящая линия,
    // но не раньше собственного start_time. Синхрон «линия готова → айтем».
    const incomingTarget = edges
      .filter((e) => e.to === node.id)
      .reduce((m, e) => Math.max(m, e.target_time ?? 0), 0);
    const appear = Math.max(node.start_time ?? 0, incomingTarget);

    return { ...node, x, y, _layer: layer, _maxLayer: maxLayer, _appear: appear };
  });

  // Габариты диаграммы: размах центров + полный размер ноды, чтобы ноды
  // гарантированно оставались внутри (раньше высота нод не учитывалась — нижний
  // ряд мог вылезать за контейнер). Ширина ноды: core 220, input/output 200.
  const nodeW = props.mobile ? 200 : 220;
  const nodeH = props.mobile ? 96 : 108;
  const bounds = {
    width: maxX - minX + nodeW,
    height: maxY - minY + nodeH,
  };

  return { nodes: layoutNodes, edges, bounds };
});

function indexOf(id: string, nodeIds: string[]) {
  return nodeIds.indexOf(id);
}

const nodes = computed(() => processedData.value.nodes);
const edges = computed(() => processedData.value.edges);
const bounds = computed(() => processedData.value.bounds);
const dataFlowEnabled = computed(() =>
  Boolean(props.showDataFlow ?? props.show_data_flow),
);

// Доступная площадь канваса измеряется ResizeObserver'ом, чтобы диаграмма
// заполняла 16:9-кадр (раньше фиксированные 800×400 оставляли мёртвые поля и
// визуально «прижимали» схему вверх). Масштаб умеет и увеличивать (до 1.6).
const canvasRef = ref<HTMLElement | null>(null);
const availW = ref(props.mobile ? 360 : 900);
const availH = ref(props.mobile ? 520 : 400);

const fitScale = computed(() => {
  if (!bounds.value) return 1;
  const pad = 24;
  const scaleX = (availW.value - pad) / Math.max(1, bounds.value.width);
  const scaleY = (availH.value - pad) / Math.max(1, bounds.value.height);
  const max = props.mobile ? 1.2 : 1.6;
  return Math.min(max, Math.max(0.35, Math.min(scaleX, scaleY)));
});

// Fallback to default schema if no nodes
const hasNodes = computed(() => nodes.value.length > 0);

const getAnimProgress = (node: any) => {
  // Появление внахлёст концу линии: fade 300мс центрирован на момент
  // дорисовки (старт за 150мс до) — глаз видит simultaneity, паузы нет.
  const t = node._appear ?? node.start_time ?? 0;
  const p = Math.min(1, Math.max(0, (relativeTime.value - t + 150) / 300));
  return 1 - Math.pow(1 - p, 3); // easeOutCubic
};

const isConnectionVisible = (conn: any) => {
  const t = conn.start_time ?? 0;
  return relativeTime.value >= t;
};

// --- РЕФЫ И SVG ПУТИ ---
// Пути теперь вычисляются чисто математически на основе node.x и node.y,
// без использования DOM getBoundingClientRect, что предотвращает зависания (deadlocks)
// в headless браузере (Playwright VirtualTime) при переключении v-show.

const getDrawOffset = (path: any) => {
  if (!path || path.start_time === undefined) return 0;
  if (!dataFlowEnabled.value || isHeadlessRender.value) return 0;
  const duration = path.target_time - path.start_time;
  if (duration <= 0) return 0;
  const progress = Math.max(
    0,
    Math.min(1, (relativeTime.value - path.start_time) / duration),
  );
  const L = pathLen(path);
  return L - progress * L;
};

const computedPaths = computed(() => {
  const nodeMap = new Map(nodes.value.map((n: any) => [n.id, n]));
  const paths = [];

  for (const conn of edges.value) {
    const startNode = nodeMap.get(conn.from);
    const endNode = nodeMap.get(conn.to);

    if (!startNode || !endNode) continue;

    let d = "";
    let length = 0;
    if (props.mobile) {
      // Вертикальные кривые под вертикальный поток (см. layoutNodes выше)
      const sx = startNode.x;
      const ex = endNode.x;
      let sy, ey;
      if (startNode.y <= endNode.y) {
        sy = startNode.y + 40;
        ey = endNode.y - 40;
      } else {
        sy = startNode.y - 40;
        ey = endNode.y + 40;
      }
      const cy = (sy + ey) / 2;
      d = `M ${sx} ${sy} C ${sx} ${cy}, ${ex} ${cy}, ${ex} ${ey}`;
      length = Math.abs(ex - sx) + Math.abs(ey - sy) + 100;
    } else {
      const sy = startNode.y;
      const ey = endNode.y;
      let sx, ex;
      if (startNode.x <= endNode.x) {
        sx = startNode.x + 110;
        ex = endNode.x - 110;
      } else {
        sx = startNode.x - 110;
        ex = endNode.x + 110;
      }
      const cx = (sx + ex) / 2;
      d = `M ${sx} ${sy} C ${cx} ${sy}, ${cx} ${ey}, ${ex} ${ey}`;
      length = Math.abs(ex - sx) + Math.abs(ey - sy) + 100;
    }

    paths.push({
      id: `${conn.from}-${conn.to}`,
      d,
      length,
      color: conn.color || "color-secondary",
      animation: conn.animation || "particles",
      start_time: conn.start_time,
      target_time: conn.target_time,
    });
  }
  return paths;
});

let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  measurePaths();
  if (
    typeof ResizeObserver !== "undefined" &&
    canvasRef.value
  ) {
    resizeObserver = new ResizeObserver((entries) => {
      const rect = entries[0]?.contentRect;
      if (!rect) return;
      if (rect.width > 0) availW.value = rect.width;
      if (rect.height > 0) availH.value = rect.height;
    });
    resizeObserver.observe(canvasRef.value);
  }
});

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect();
});

// Точная длина пути из геометрии SVG (оценка «манхэттен+100» врёт на
// кривых S-ishing: линия визуально завершалась раньше расчёта — и нода
// хлопала с запозданием). getTotalLength — чистая геометрия без layout,
// под VirtualTime-рендером безопасен. id скоупим на инстанс: диаграмм
// на странице несколько (v-show), getElementById иначе бьёт мимо.
const uid = Math.random().toString(36).slice(2, 8);
const pathDomId = (path: any) => `path-${uid}-${path.id}`;
const measuredLengths = ref<Record<string, number>>({});

const measurePaths = () => {
  nextTick(() => {
    for (const p of computedPaths.value) {
      const el = document.getElementById(pathDomId(p)) as unknown as SVGPathElement | null;
      if (!el || typeof el.getTotalLength !== "function") continue;
      try {
        const L = el.getTotalLength();
        if (L > 0) measuredLengths.value[p.id] = L;
      } catch {
        /* ignore — остаёмся на оценке */
      }
    }
  });
};

watch(computedPaths, measurePaths, { flush: "post" });

// Длина для dash draw-on: замеренная, иначе оценка из layoutNodes.
const pathLen = (path: any) =>
  measuredLengths.value[path.id] || path.length;

const getNodeType = (node: any) => {
  if (node.is_main === true) return "core";
  if (node.is_main === false) {
    return node._layer <= node._maxLayer / 2 ? "input" : "output";
  }
  if (node.type === "core") return "core";
  if (node.type) return node.type;
  if (node._maxLayer === 0) return "core";
  if (node._layer === 0) return "input";
  if (node._layer === node._maxLayer) return "output";
  return "core";
};
</script>

<template>
  <div
    class="architecture-diagram-container relative mx-auto overflow-hidden w-full max-w-6xl h-full min-h-0 flex flex-col"
    :style="{
      ...itemVars,
      ...itemPrimaryVars,
      background: 'var(--item-bg)',
      backdropFilter: 'var(--item-backdrop)',
      WebkitBackdropFilter: 'var(--item-backdrop)',
      borderRadius: 'var(--item-radius)',
      boxShadow: 'var(--item-shadow)',
      padding: 'var(--item-padding)',
      borderWidth: 'var(--item-border-width)',
      borderStyle: 'var(--item-border-style)',
      borderColor: 'var(--item-border)',
    }"
  >
    <div
      ref="canvasRef"
      class="relative flex-1 min-h-0 w-full overflow-hidden"
    >
      <div
        v-if="hasNodes"
        class="absolute inset-0 flex items-center justify-center"
      >
        <div
          class="relative w-full h-full"
          :style="{
            transform: `scale(${fitScale})`,
            transformOrigin: 'center center',
          }"
        >
        <!-- SVG слой с путями и пакетами данных -->
        <svg
          class="absolute z-0 pointer-events-none overflow-visible"
          style="left: 50%; top: 50%"
        >
          <g v-for="(path, i) in computedPaths" :key="'static-' + path.id">
            <template v-if="isConnectionVisible(path)">
              <!-- Статическая фоновая ниточка в цвете исходной ноды (как раньше),
                   ширина/поведение из варианта; появление — draw-on -->
              <path
                :id="pathDomId(path)"
                :d="path.d"
                fill="none"
                :stroke="path.color"
                :stroke-width="(Number(line.width) || 2) + 0.6"
                :stroke-dasharray="
                  line.dash === 'none' ? pathLen(path) : line.dash
                "
                :style="{
                  opacity: flowAnimation(path) === 'none' ? 1 : 0.65,
                  strokeDashoffset:
                    line.dash === 'none' ? getDrawOffset(path) : (40 - ((relativeTime % 2000) / 2000 * 40)),
                }"
              />

              <template v-if="shouldAnimateFlow && flowAnimation(path) !== 'none'">
                <path
                  v-if="flowAnimation(path) === 'particles'"
                  :d="path.d"
                  fill="none"
                  :stroke="path.color"
                  stroke-width="6"
                  stroke-linecap="round"
                  stroke-dasharray="0 10000"
                  :style="{
                    strokeDashoffset:
                      -(
                        (relativeTime % (2000 + (i % 2) * 500)) /
                        (2000 + (i % 2) * 500)
                      ) * path.length,
                    filter: 'drop-shadow(0 0 4px currentColor)',
                  }"
                />

                <path
                  v-else-if="flowAnimation(path) === 'dash'"
                  :d="path.d"
                  fill="none"
                  :stroke="path.color"
                  :stroke-width="line.width"
                  stroke-linecap="round"
                  :stroke-dasharray="line.dash === 'none' ? '6 12' : line.dash"
                  :style="{
                    strokeDashoffset: 40 - ((relativeTime % 2000) / 2000 * 40)
                  }"
                />

                <path
                  v-else-if="flowAnimation(path) === 'pulse'"
                  :d="path.d"
                  fill="none"
                  :stroke="path.color"
                  :stroke-width="line.width"
                  stroke-linecap="round"
                  :style="{
                    opacity:
                      0.2 +
                      0.8 *
                        (Math.sin((relativeTime / 2000) * Math.PI * 2) * 0.5 +
                          0.5),
                    filter:
                      'drop-shadow(0 0 ' +
                      8 *
                        (Math.sin((relativeTime / 2000) * Math.PI * 2) * 0.5 +
                          0.5) +
                      'px currentColor)',
                  }"
                />

                <path
                  v-else-if="flowAnimation(path) === 'solid'"
                  :d="path.d"
                  fill="none"
                  :stroke="path.color"
                  :stroke-width="line.width"
                  stroke-linecap="round"
                />
              </template>
            </template>
          </g>
        </svg>

        <!-- УЗЛЫ (Absolute Positioning based on BFS x,y) -->
        <div class="absolute inset-0 w-full h-full z-10">
          <div
            v-for="(node, nIdx) in nodes"
            :key="node.id"
            class="absolute -translate-x-1/2 -translate-y-1/2"
            :style="{
              left: `calc(50% + ${node.x}px)`,
              top: `calc(50% + ${node.y}px)`,
            }"
          >
            <!-- INPUT/OUTPUT STYLE -->
            <div
              v-if="getNodeType(node) !== 'core'"
              class="node variant-item flex items-center"
              :class="[mobile ? 'w-[170px]' : 'w-[200px]']"
              :style="{
                ...nodeStyle,
                borderColor: getColorAlpha(node.color, 0.4),
                opacity: getAnimProgress(node),
                transform: `scale(${0.9 + 0.1 * getAnimProgress(node)})`,
              }"
            >
              <div
                class="w-10 h-10 flex items-center justify-center shrink-0"
                :style="{
                  backgroundColor: getColorAlpha(node.color, 0.15),
                  color: getHexColor(node.color),
                  borderRadius: 'calc(var(--item-radius) - 4px)',
                }"
              >
                <Icon
                  v-if="
                    node.icon &&
                    !['telegram', 'web', 'db', 'api'].includes(node.icon)
                  "
                  :icon="
                    node.icon.includes(':') ? node.icon : 'lucide:' + node.icon
                  "
                  class="text-lg"
                />
                <svg
                  v-else-if="node.icon === 'telegram'"
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="m22 2-7 20-4-9-9-4Z" />
                  <path d="M22 2 11 13" />
                </svg>
                <svg
                  v-else-if="node.icon === 'web'"
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
                  <line x1="3" x2="21" y1="9" y2="9" />
                  <line x1="9" x2="9" y1="21" y2="9" />
                </svg>
                <svg
                  v-else-if="node.icon === 'db'"
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <ellipse cx="12" cy="5" rx="9" ry="3" />
                  <path d="M3 5V19A9 3 0 0 0 21 19V5" />
                  <path d="M3 12A9 3 0 0 0 21 12" />
                </svg>
                <svg
                  v-else-if="node.icon === 'api'"
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"
                  />
                  <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                  <line x1="12" y1="22.08" x2="12" y2="12" />
                </svg>
                <!-- Default fallback icon -->
                <svg
                  v-else
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
                </svg>
              </div>
              <div class="min-w-0">
                <div
                  class="font-heading font-bold text-text-primary leading-tight line-clamp-2 text-balance break-words"
                  :class="mobile ? 'text-xs' : 'text-sm'"
                >
                  {{ node.title }}
                </div>
                <div
                  class="font-sans font-bold uppercase mt-0.5 line-clamp-2 text-balance break-words"
                  :class="[mobile ? 'text-[8px]' : 'text-[10px]']"
                  :style="{ color: getHexColor(node.color) }"
                >
                  {{ node.subtitle }}
                </div>
              </div>
            </div>

            <!-- CORE STYLE -->
            <div
              v-else
              class="node variant-item flex flex-col items-center"
              :class="[mobile ? 'w-[200px]' : 'w-[220px]']"
              :style="{
                ...nodeStyle,
                borderColor: getColorAlpha(node.color, 0.4),
                opacity: getAnimProgress(node),
                transform: `scale(${0.9 + 0.1 * getAnimProgress(node)})`,
              }"
            >
              <div
                class="w-12 h-12 rounded-full border flex items-center justify-center"
                :style="{
                  backgroundColor: getColorAlpha(node.color, 0.15),
                  borderColor: getColorAlpha(node.color, 0.4),
                  color: getHexColor(node.color),
                }"
              >
                <Icon
                  v-if="node.icon"
                  :icon="
                    node.icon.includes(':') ? node.icon : 'lucide:' + node.icon
                  "
                  class="text-2xl"
                />
                <svg
                  v-else
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <rect width="16" height="16" x="4" y="4" rx="2" ry="2" />
                  <rect width="6" height="6" x="9" y="9" rx="1" ry="1" />
                  <path d="M9 1v3" />
                  <path d="M15 1v3" />
                  <path d="M9 20v3" />
                  <path d="M15 20v3" />
                  <path d="M20 9h3" />
                  <path d="M20 14h3" />
                  <path d="M1 9h3" />
                  <path d="M1 14h3" />
                </svg>
              </div>
              <div
                class="font-heading font-bold text-lg text-text-primary text-center leading-tight line-clamp-2 text-balance break-words"
              >
                {{ node.title }}
              </div>
              <div
                class="text-xs font-sans font-bold uppercase text-center line-clamp-2 text-balance break-words"
                :style="{ color: getHexColor(node.color) }"
              >
                {{ node.subtitle }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

      <div v-else class="absolute inset-0 flex items-center justify-center text-text-muted text-sm font-mono">
        Пожалуйста, добавьте узлы в редакторе JSON.
      </div>
    </div>
  </div>
</template>

<style scoped>
.anim-dash {
  stroke-dasharray: 6 12;
}

@keyframes dash-flow {
  from {
    stroke-dashoffset: 18;
  }
  to {
    stroke-dashoffset: 0;
  }
}

.anim-pulse {
}

@keyframes pulse-flow {
  0%,
  100% {
    opacity: 0.2;
  }
  50% {
    opacity: 1;
    filter: drop-shadow(0 0 8px currentColor);
  }
}
</style>
