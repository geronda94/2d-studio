export type BeforeAfterAction = 'setSlider'

export interface BeforeAfterEvent {
  time: number
  action: BeforeAfterAction
  value: number // от 0 до 100
  duration?: number // Время анимации в мс (по умолчанию 1000)
}

export type InteractiveArchitectureAction = 'panTo' | 'hoverNode' | 'resetView'

export interface InteractiveArchitectureEvent {
  time: number
  action: InteractiveArchitectureAction
  nodeId?: string
  zoom?: number
  duration?: number
}

export type ModernTableAction = 'highlightRow' | 'tooltipCell' | 'clear'

export interface ModernTableEvent {
  time: number
  action: ModernTableAction
  rowIndex?: number
  colKey?: string
}

// По мере перевода остальных компонентов сюда добавятся их интерфейсы

export type TechStackAction = 'highlight' | 'clear'

export interface TechStackEvent {
  time: number
  action: TechStackAction
  itemId?: string
}

// --- Roadmap ---
export type RoadmapAction = 'setStep'

export interface RoadmapEvent {
  time: number
  action: RoadmapAction
  stepIndex: number
}

export type ProcessFunnelAction = 'showStage'

export interface ProcessFunnelEvent {
  time: number
  action: ProcessFunnelAction
  stageIndex: number
}

export type PremiumChecklistAction = 'showItem'

export interface PremiumChecklistEvent {
  time: number
  action: PremiumChecklistAction
  itemIndex: number
}

// --- Terminal Mockup ---
export type TerminalMockupAction = 'start' | 'clear'

export interface TerminalMockupEvent {
  time: number
  action: TerminalMockupAction
}

// --- Network Waterfall ---
export type NetworkWaterfallAction = 'start' | 'clear'

export interface NetworkWaterfallEvent {
  time: number
  action: NetworkWaterfallAction
}

// --- Code Explain ---
export type CodeExplainAction = 'highlight' | 'clear'

export interface CodeExplainEvent {
  time: number
  action: CodeExplainAction
  index?: number
}

// --- Spaghetti Diagram ---
export type SpaghettiAction = 'highlight' | 'clear'

export interface SpaghettiEvent {
  time: number
  action: SpaghettiAction
  nodeId?: number // индекс элемента
}

// --- Clean Bento Diagram ---
export type CleanBentoAction = 'highlight' | 'clear'

export interface CleanBentoEvent {
  time: number
  action: CleanBentoAction
  nodeId?: string // например 'presentation-0', 'domain-1', 'infra-2'
}

