# Desktop QA defects — /p/63 (kitchen-sink, all components)

Собрано 6 ревьюерами по скриншотам `uploads/qa_full/` (1920×1080, реальные кадры).
Формат: `idx | Slug | severity | defect | suggested fix`.

## Системные корни
1. **Пустой кадр**: контент не заполняет 16:9, верх-тяжёлый, снизу мёртвая зона. Нужно тянуть контент на всю высоту (`h-full` + `flex-1` + центрирование/увеличение).
2. **Битые чарты/диаграммы**: нет осей/базлайна, пустые канвасы, ноды уехали/обрезаны, нет коннекторов.
3. **Клиппинг таблиц**: последние строки срезаны снизу, футер наезжает.
4. **Битые данные/плейсхолдеры** (часть — в `scripts/build_kitchen_sink.py`): `₽`, «0 благодати», «Показатель 1/2», «Chart Area Placeholder», чёрное видео, битые аватары, только 3 карточки и т.п.

---

## BATCH 1 — Plots / charts
```
000 | AbcXyzMatrix | HIGH | Left scatter panel completely empty — no bubbles | recompute points/scale so all SKUs render inside plot
000 | AbcXyzMatrix | HIGH | only one bubble "SKU-1003", clipped by top border | fix coordinates/scale
000 | AbcXyzMatrix | MED | legend contradicts table (Класс C 1 but no C rows) | derive counts from data
000 | AbcXyzMatrix | LOW | both panels ~90% dead space | tighten plot/enlarge bubbles
049 | ItemAnalysis | MED | Y-axis 80% tick mispositioned; intermediate ticks missing | recompute ticks
049 | ItemAnalysis | LOW | orange trend line runs to edge at 100% | anchor to data
049 | ItemAnalysis | LOW | bars labeled non-sequentially (№1,№5,№2,№3,№4) | label in chart order
075 | ParetoChart | MED | right % axis non-linear (100→80 gap >> 80→0) | linear cumulative axis
075 | ParetoChart | MED | cumulative line crosses "9 мин" label | offset labels
075 | ParetoChart | LOW | no left Y-axis (minutes) | add axis
066 | NetworkWaterfall | MED | axis ticks shifted left; bars don't align with axis | align plot origin
066 | NetworkWaterfall | LOW | dead band above first bar | reduce header gap
097 | SCurve | HIGH | plot lines clipped at right edge | add right padding
097 | SCurve | MED | Y-axis no numeric labels | add labels
097 | SCurve | LOW | no left margin/axis title | add
074 | PaceBoard | MED | no Y-axis labels | add
074 | PaceBoard | MED | plan line clipped top-right | extend Y domain
065 | MoralDecline | HIGH | x-axis equally spaced despite unequal years | scale by real intervals
065 | MoralDecline | MED | no y-axis scale | add
065 | MoralDecline | LOW | line runs off right edge | inset
065 | MoralDecline | LOW | gap between plot and axis labels | attach labels
110 | StatsBarChart | MED | 4 wide bars, huge gaps | more points / cap width
110 | StatsBarChart | MED | header "Last 7 Days" vs bars ЯНВ–АПР | relabel
110 | StatsBarChart | LOW | gridlines 67/33 non-round | clean scale
112 | StudentGrowth | MED | label "84" crossed by threshold line | offset label
112 | StudentGrowth | LOW | band label low contrast | raise
112 | StudentGrowth | LOW | only 100/0 gridlines | add mid ticks
130 | YamazumiBalance | MED | takt label collides with frame edge | move inside
130 | YamazumiBalance | MED | station 3 value "34 с" on takt line | offset
130 | YamazumiBalance | LOW | bars no baseline | anchor
130 | YamazumiBalance | LOW | delta chips low contrast/no legend | fix
099 | SafetyDashboard | HIGH | bar chart overlaps metric panels | separate sections
099 | SafetyDashboard | HIGH | bars clip panels' bottom border | reserve space
099 | SafetyDashboard | MED | y-axis only 100/80/0 | full scale
099 | SafetyDashboard | MED | empty area at bottom | rebalance
063 | MetricScales | LOW | 3 short rows, big empty bands | increase row height
044 | HeatmapMatrix | LOW | grid sits high, empty bottom | center
044 | HeatmapMatrix | LOW | caption low contrast | raise
044 | HeatmapMatrix | LOW | cell letters tiny | increase
129 | WorldviewMatrix | MED | empty band below matrix | center
129 | WorldviewMatrix | LOW | too many hues | constrain palette
129 | WorldviewMatrix | LOW | footnote low contrast | raise
023 | CohortGrid | MED | ~280px empty below table | center/enlarge
023 | CohortGrid | LOW | caption detached | move adjacent
089 | RadarProfile | MED | radar ~20% of canvas | enlarge
117 | TheologicalSchools | HIGH | radar floats, huge margins | enlarge
117 | TheologicalSchools | MED | muddy overlapping polygons | reduce fill opacity
117 | TheologicalSchools | LOW | axis labels tiny/low contrast | raise
127 | VirtuesRadar | HIGH | radar floats, huge margins | enlarge
127 | VirtuesRadar | MED | series indistinguishable | increase stroke/contrast
127 | VirtuesRadar | LOW | axis labels tiny | raise
127 | VirtuesRadar | LOW | footnote low contrast | raise
086 | QuadrantMatrix | MED | bubbles tiny, quadrants empty | scale bubbles
086 | QuadrantMatrix | LOW | y-axis label collides | move out
086 | QuadrantMatrix | LOW | quadrant titles low contrast | raise
```

## BATCH 2 — Networks / diagrams A
```
005 | ArchitectureDiagram | MED | diagram shifted up, bottom third empty | vertically center
005 | ArchitectureDiagram | LOW | dashed connectors faint | increase width/opacity
048 | InteractiveArchitecture | HIGH | nodes clipped by container bottom | fix auto-layout
048 | InteractiveArchitecture | HIGH | layout collapses to bottom, ~60% empty above | recompute/center
048 | InteractiveArchitecture | MED | minimap overlaps node | reposition
048 | InteractiveArchitecture | MED | zoom control overlaps node | move
067 | NodeFlow | HIGH | single thin row, ~15% of frame | enlarge/stack stages
067 | NodeFlow | MED | connector captions overlap nodes, tiny | dedicated space, raise
042 | HabitLoop | HIGH | node captions overlap cards/connectors | offset captions
042 | HabitLoop | MED | central loop icon small/unlabeled | enlarge+label
042 | HabitLoop | MED | diagram occupies small central area | scale up
018 | ChurchAsBody | HIGH | no connectors center→nodes | draw links
018 | ChurchAsBody | MED | "Евангели..." truncated | widen
018 | ChurchAsBody | MED | clustered center, huge margins | rebalance radii
018 | ChurchAsBody | LOW | empty bottom third | center
033 | EcosystemSlide | HIGH | central visual broken (white bar + dark rect) | fix/replace
033 | EcosystemSlide | HIGH | no connectors center→nodes | draw radial links
033 | EcosystemSlide | MED | nodes at corners, huge gaps | tighten
046 | InfluenceMap | HIGH | legend prints raw node IDs | human labels
046 | InfluenceMap | MED | diagram crammed upper half | center
051 | KnowledgeGraph | HIGH | legend prints raw IDs | human labels
051 | KnowledgeGraph | LOW | legend hugs bottom, gap above | tighten
060 | MapVisualization | HIGH | bare grid, no map | add map background
060 | MapVisualization | MED | markers clustered in band | spread
060 | MapVisualization | LOW | route line overlaps "Казань" | offset
092 | RelicsMap | HIGH | top markers clipped by container top | padding/reposition
092 | RelicsMap | MED | markers clustered left, right empty | distribute
092 | RelicsMap | LOW | labels flush on circles | spacing
105 | SiteLogisticsMap | MED | node icon overlaps pill | fix positions
105 | SiteLogisticsMap | MED | connector labels crowd center | reposition
105 | SiteLogisticsMap | LOW | empty right/bottom | spread
039 | FloorPlanZones | HIGH | zone5 label overlaps legend | reposition
039 | FloorPlanZones | HIGH | center label overlaps node2; icon faint | reposition/opacity
039 | FloorPlanZones | MED | markers arbitrary, no plan geometry | anchor to plan
107 | SoulStructure | LOW | diagram small, big margins | enlarge
107 | SoulStructure | LOW | connectors at corners not edges | attach to edges
123 | ValueStreamMap | MED | captions overlap pills | gap/mid-span
123 | ValueStreamMap | MED | empty bands break rhythm | tighten
123 | ValueStreamMap | LOW | bottom metrics row tiny/low contrast | raise
```

## BATCH 3 — Diagrams B / timelines
```
040 | GanttChart | HIGH | "Обучение команды" full bar labeled 0% | fix value/fill
040 | GanttChart | MED | milestone diamonds float, no baseline | align to timeline
040 | GanttChart | LOW | % labels tiny/inconsistent | standardize
119 | TimelineSlide | HIGH | active event content missing | render active content
119 | TimelineSlide | HIGH | ghost label near-invisible | contrast
119 | TimelineSlide | MED | timeline pinned to bottom | lift
119 | TimelineSlide | LOW | rightmost node barely visible | raise
118 | TimelineEras | MED | ~280px empty bottom | rebalance
118 | TimelineEras | LOW | line protrudes past last node | terminate
113 | SustainabilityTimeline | LOW | connector color inconsistent | drive from node
077 | PersecutionWaves | MED | huge empty top/bottom, band ~30% | enlarge/spread
077 | PersecutionWaves | LOW | axis extends beyond nodes | trim
109 | StagesOfSin | MED | % badges float, fragmented lines | continuous connectors
109 | StagesOfSin | MED | empty gap labels→legend | tighten
109 | StagesOfSin | LOW | stage1 no badge | add baseline
109 | StagesOfSin | LOW | legend uneven | equalize
094 | Roadmap | MED | occupies middle third, huge bands | enlarge/center
094 | Roadmap | LOW | last node label white vs colored | consistent
050 | JourneyMap | MED | top-heavy, ~290px empty bottom | center
056 | LessonArc | MED | top-heavy, ~290px empty bottom | center
043 | HandoverMatrix | MED | odd column order, bars tiny/misaligned | single ordered list
043 | HandoverMatrix | LOW | top progress bar tiny stub | lengthen
059 | MaintenanceBoard | MED | board top half, ~200px gap | center
078 | PipelineBoard | MED | first column no badge | consistent
078 | PipelineBoard | MED | cards ~150px below content | reduce height
078 | PipelineBoard | LOW | header truncated | shorten
106 | SnagBoard | HIGH | last column card clipped | fit
106 | SnagBoard | MED | columns sparse | rebalance
058 | MachineStatusBoard | HIGH | second-row cards clipped | fit
058 | MachineStatusBoard | HIGH | footer overlaps clipped cards | reflow
058 | MachineStatusBoard | MED | 2 cards row2, right empty | balance
071 | OrgChart | MED | tree shifted right, left third empty | center/scale
071 | OrgChart | LOW | "1 функций" grammar | pluralize
041 | GenealogyTree | MED | dangling connector to empty area | remove/terminate
041 | GenealogyTree | LOW | first card narrower | equalize
111 | StepByStep | HIGH | chain centered-low, ~third empty | center/enlarge
111 | StepByStep | LOW | ragged description wrapping | equalize
082 | ProcessFunnel | HIGH | only 3 stages, thin band, empty | add 4th, enlarge
082 | ProcessFunnel | MED | connectors detached, no funnel shape | flush + taper
061 | MarketSizing | HIGH | SOM unlabeled | add label
061 | MarketSizing | MED | nested rects bottom-anchored | center
061 | MarketSizing | LOW | source note low contrast | raise
```

## BATCH 4 — Tables / lists
```
004 | ArchaeologyConfirms | HIGH | table overflows bottom, row4 cut | reduce height/split
004 | ArchaeologyConfirms | HIGH | footer on top of clipped row | reserve space
004 | ArchaeologyConfirms | MED | uneven row heights | normalize
012 | BoqSmeta | HIGH | table clipped at bottom | paginate/shrink
012 | BoqSmeta | HIGH | summary bar overlaps clipped rows | reserve space
012 | BoqSmeta | LOW | header count wrong | fix count
014 | ChangeOrderLog | HIGH | left table clipped | fit
014 | ChangeOrderLog | HIGH | right bubble chart broken (no axes, orphan €0) | rebuild
014 | ChangeOrderLog | MED | heavy truncation | widen/shorten
014 | ChangeOrderLog | MED | "-58 000"/"+47 000" overlap | adjust
014 | ChangeOrderLog | MED | footer overlaps clipped row | reserve
068 | NotationTable | MED | last summary row flush/clipped | bottom padding
108 | SpecTable | LOW | table low/off-center | center
108 | SpecTable | LOW | value column color inconsistent | unify
125 | ValuesTable | MED | ~250px empty below table | enlarge
125 | ValuesTable | LOW | uneven row heights | fix
008 | AssessmentBlueprint | MED | НАВЫК column truncated | widen
008 | AssessmentBlueprint | MED | "Итого" 35 in % column | move to БАЛЛОВ
008 | AssessmentBlueprint | LOW | gap footer→DOK bar | tighten
031 | CurriculumMap | MED | ragged grid, empty cells | fill/N/A
031 | CurriculumMap | LOW | course label truncated | widen
037 | FineTuningScales | MED | legend descriptions truncated | widen
037 | FineTuningScales | LOW | micro-text tiny, gaps | raise
080 | PremiumChecklist | MED | last card taller, breaks grid | equalize
080 | PremiumChecklist | LOW | gap divider→cards | tighten
081 | PricingTable | MED | middle card pushed down by badge | reserve space
081 | PricingTable | LOW | side cards 3 vs 4 features | balance
064 | ModernTable | HIGH | "120K ₽" ruble | €
064 | ModernTable | LOW | big empty bands | rebalance
076 | PassionsVirtues | HIGH | first/last rows clipped | fit
053 | LadderOfVirtues | MED | step1 text truncated | shorten/widen
053 | LadderOfVirtues | LOW | step numbering confusing | align
035 | FamilyOrder | MED | dividers/refs misaligned | equalize
102 | ScriptureParallel | MED | ~200px empty bottom in cards | reduce height
098 | SacredNumbers | LOW | row4 chip wraps | uniform
098 | SacredNumbers | LOW | unused right gap | fill/center
057 | LoveTypes | LOW | watermark icons look like smudges | opacity/remove
057 | LoveTypes | LOW | columns 1&2 similar orange | distinct
101 | ScienceFaithParallel | HIGH | bottom caption clipped | fit
101 | ScienceFaithParallel | MED | mismatched card heights, arrows misaligned | equalize
101 | ScienceFaithParallel | MED | 4 pairs overflow | tighten
085 | ProphecyFulfillment | HIGH | third row right card clipped | fit
085 | ProphecyFulfillment | LOW | uneven row heights | clamp
096 | RulerCompare | LOW | uneven row heights | equalize
```

## BATCH 5 — Cards / content A
```
002 | AnimatedStatsSlide | MED | 3rd card alone row2, unbalanced | 3-across
002 | AnimatedStatsSlide | MED | sparkline through digits | offset/backing
002 | AnimatedStatsSlide | LOW | sparkline clipped by borders | padding
047 | InfographicCards | HIGH | only 3 cards (need 4) | add 4th
047 | InfographicCards | MED | 3rd card no icon, misaligned | add icon/align
047 | InfographicCards | MED | big empty bands | enlarge/center
010 | BentoGridGallery | HIGH | subtitle clipped by card bottom | height/font
010 | BentoGridGallery | MED | empty hole bottom-right | rebalance spans
010 | BentoGridGallery | MED | subtitles flush bottom edge | padding
010 | BentoGridGallery | MED | white titles on bright images | scrim
011 | BloomLadder | MED | level1 subtitle truncated | widen
011 | BloomLadder | LOW | tag chips wrap unevenly | one line/equalize
027 | ConceptDiptych | HIGH | lower 40% empty | scale/center
027 | ConceptDiptych | MED | asymmetric columns 3 vs 2 | balance
029 | CosmologyGenesis | MED | ~250px dead gap | tighten
029 | CosmologyGenesis | MED | connectors detached, badges overlap | connect/reposition
030 | CrmCardSlide | HIGH | "150 000 ₽" ruble | €
015 | CharacterStats | MED | generic placeholder avatar, card empty | real image/shrink
015 | CharacterStats | LOW | empty below name | rebalance
016 | ChatMockupSlide | MED | left half empty | rebalance/center
016 | ChatMockupSlide | LOW | dialogue ends on user | end on bot
016 | ChatMockupSlide | LOW | baboon photo tone mismatch | replace
021 | CodeComparisonSlide | MED | right window short, asymmetric | equalize heights
021 | CodeComparisonSlide | LOW | left block near bottom edge | margin
022 | CodeExplain | LOW | empty band bottom, top-heavy | shrink/center
036 | FigureCard | MED | empty placeholder "Фото объекта" | image asset
036 | FigureCard | MED | "0 благодати" zero not letter О | fix data
038 | FlashCards | LOW | answers with no question; ОТВЕТ low contrast | show Q/raise
045 | HistoricalCompare | HIGH | broken-image placeholders both sides | real media/empty-state
045 | HistoricalCompare | MED | huge dead space in cards | shrink media/center
052 | KpiDashboard | LOW | trend badges overlap sparkline ends | reserve space
052 | KpiDashboard | LOW | big empty margins | enlarge/rebalance
069 | ObjectPassport | HIGH | main title truncated | wrap 2 lines
069 | ObjectPassport | MED | lower half empty | move footer/enlarge
072 | OrganicGrid | MED | large tiles bottom-anchor text, watermark invisible | top-align/opacity
072 | OrganicGrid | LOW | security tile hugs bottom | margin
073 | OutroSlide | MED | logo low contrast on dark | backing/glow
073 | OutroSlide | LOW | unbalanced logo vs QR | scale/rebalance
```
(AnimatedStatsSlide, InfographicCards, BentoGridGallery, BloomLadder, ConceptDiptych, CosmologyGenesis, CrmCardSlide, CharacterStats, ChatMockupSlide, CodeComparisonSlide, CodeExplain, FigureCard, FlashCards, HistoricalCompare, KpiDashboard, ObjectPassport, OrganicGrid, OutroSlide)

## BATCH 6 — Cards / content B
```
079 | PortraitLampSlide | MED | portrait missing (placeholder "Портрет") | image/placeholder
079 | PortraitLampSlide | MED | lower frame empty | center/enlarge
079 | PortraitLampSlide | LOW | lamp below arch near bottom | raise
083 | ProductCard | LOW | gap feature list→CTA | reduce height
083 | ProductCard | LOW | white top strip clashes | dark asset
084 | ProgressScalesSlide | HIGH | only 2 placeholder scales, huge empty | ≥3 real metrics
084 | ProgressScalesSlide | MED | placeholder names | real content
090 | ReceiptCard | LOW | left title column half empty | align/fill
091 | ReconciliationPath | MED | cards full width, text left 40% | narrow/two-col
100 | SaintQuote | HIGH | broken author avatar | valid image/initials
100 | SaintQuote | LOW | empty bottom in card | reduce height
103 | SeedAndSoil | MED | card1 bar nearly invisible | min bar height
103 | SeedAndSoil | MED | stray unlabeled dashes | label/remove
103 | SeedAndSoil | LOW | empty above bars | scale bars
104 | ShiftHandover | MED | panels half empty bottom | reduce/add content
104 | ShiftHandover | LOW | unequal panel heights | align
114 | TeamGrid | MED | cards float, ~220/260px empty | enlarge/recenter
114 | TeamGrid | LOW | inconsistent contact icons | consistent
115 | TechStackSlide | HIGH | 3 cards float, ~300px empty | enlarge/add/spread
121 | UnitEconomics | MED | payback bar 100% no marker | scale+mark
121 | UnitEconomics | MED | thin middle band | enlarge
121 | UnitEconomics | LOW | € glyph odd | font fallback
122 | UseOfFunds | MED | bottom-right quadrant empty | balance
122 | UseOfFunds | LOW | donut "€3М" cramped | spacing
124 | ValuesOfEpochs | LOW | isolated footnote | move closer
124 | ValuesOfEpochs | LOW | line protrudes past last node | terminate
126 | VerseFocus | LOW | highlight box flush right edge | padding
106 | SnagBoard | (see batch3)
006 | ArgumentStructure | MED | steps left half, right empty | full width/rebalance
006 | ArgumentStructure | MED | big gap step3→bottom boxes | distribute
009 | BeforeAfterSlide | MED | "ПОСЛЕ" is right crop of same photo | distinct images
013 | BrowserMockup | MED | "Chart Area Placeholder" literal | real chart/remove
013 | BrowserMockup | MED | empty bottom | fill/reduce
013 | BrowserMockup | LOW | "$" instead of "€" | €
013 | BrowserMockup | LOW | no sidebar/nav | add chrome
019 | CircularGauge | MED | "118%" full ring misleading | cap/marker
019 | CircularGauge | MED | big empty space, content small | enlarge
020 | CivilizationCycle | LOW | center "Распад" duplicates stage4 | clarify
```

## BATCH 7 — Data (scripts/build_kitchen_sink.py)
```
030 | CrmCardSlide | HIGH | "150 000 ₽" → €
064 | ModernTable | HIGH | "120K ₽" → €
036 | FigureCard | MED | "0 благодати" → "О благодати"
084 | ProgressScalesSlide | HIGH | placeholder "Показатель 1/2" → real metrics (≥3)
047 | InfographicCards | HIGH | only 3 cards → 4
061 | MarketSizing | HIGH | SOM label missing
013 | BrowserMockup | MED | "Chart Area Placeholder" → real content; "$"→€
001 | AdvancedVideoSlide | HIGH | black video → valid media/poster
045 | HistoricalCompare | HIGH | broken images → valid assets
100 | SaintQuote | HIGH | broken avatar → valid/initials
016 | ChatMockupSlide | LOW | end dialogue on bot reply
```
