# Round-2 defects (after first fix pass) — /p/63

## Agent 1 — regressions / broken components
```
079 | PortraitLampSlide | HIGH | arch frame overlaps/clips text column (letters cut) | shrink arch or give text its own column
021 | CodeComparisonSlide | HIGH | both code windows empty (no code rendered) | verify code payload + Shiki render
024 | CohortRetention | HIGH | KPI cards overlap & clip cohort table header | reserve vertical space / push table down
043 | HandoverMatrix | HIGH | 4th matrix row clipped behind legend | reserve row height / shrink cells
076 | PassionsVirtues | HIGH | last row has no visible bar (clipped) | fit all rows / reduce spacing
086 | QuadrantMatrix | HIGH | bubbles collinear on mid line; no vertical divider | fix y-scale so points spread across quadrants
128 | WaterfallChart | HIGH | broken: labels detached below bars, no baseline, no legend | anchor labels, baseline, legend, square corners
082 | ProcessFunnel | HIGH/MED | only 3 stages + no funnel taper | taper widths + enlarge (4th stage = data agent)
```
## Agent 2 — charts / radars
```
044 | HeatmapMatrix | center vertically; caption contrast; larger cell glyphs
049 | ItemAnalysis | left y-axis ticks 92/46/0 (remove or clean); bar labels in chart order; trend line crosses 41% label
063 | MetricScales | 3 rows widely spaced, big empty bands → enlarge/center
065 | MoralDecline | round y ticks; ~350px dead band to bottom cards; "% христиан" collides top
066 | NetworkWaterfall | 0ms tick offset from plot origin; align bars to origin
075 | ParetoChart | left y-axis misaligned (bars below 0); compressed middle band; cumulative line grazes labels
097 | SCurve | plot compressed to thin band; round ticks (0/29/59/88/117)
099 | SafetyDashboard | left panel bottom empty; x labels truncated
110 | StatsBarChart | wide gaps (add points/cap width); axis max 200 vs peak 91; round gridlines; "78" on NORM line
112 | StudentGrowth | band labels low contrast; "+42 п.п." chip dim
117 | TheologicalSchools | muddy overlapping polygons; add radar scale labels
127 | VirtuesRadar | radar ~22% width → enlarge; footnote contrast
129 | WorldviewMatrix | footnote contrast; ~170px dead band
130 | YamazumiBalance | "такт" flush right edge; station3 badge on takt line; add segment legend
```
## Agent 3 — diagrams / timelines / cards dead-space
```
067 | NodeFlow | ~60% frame; captions on dashed lines
071 | OrgChart | tree right-shifted/narrow, left third empty
073 | OutroSlide | logo panel oversized/empty; handle printed twice
077 | PersecutionWaves | band ~40%; footnote contrast
078 | PipelineBoard | column cards ~300px empty middle
094 | Roadmap | large dead bands; 4th node outlined vs filled
111 | StepByStep | band ~25% of frame
115 | TechStackSlide | ~180px empty above/below icon in each card
116 | TerminalMockup | orphan diff-stat lines before prompt; ~100px empty rows
118 | TimelineEras | ~35% band; connector single blue vs multi-color nodes
119 | TimelineSlide | pinned bottom, ~250px gap; low-contrast years; right half empty
124 | ValuesOfEpochs | ~215px dead band below footnote
125 | ValuesTable | ~200px dead below; uneven rows; minus icon
126 | VerseFocus | ~185px dead above / ~225px below
102 | ScriptureParallel | ~180px dead above / ~110px below in cards
103 | SeedAndSoil | stray unlabeled dashes; empty above short bars
106 | SnagBoard | sparse middle columns
090 | ReceiptCard | left title column ~90% empty
052 | KpiDashboard | card internal empty bands
080 | PremiumChecklist | 5/6 cards have heading only, empty body
```
## Agent 4 — data (patch /p/63 payloads + seed/example sources)
```
001 | AdvancedVideoSlide | black video → valid media or poster
009 | BeforeAfterSlide | "ПОСЛЕ" = crop of same photo → distinct after image
013 | BrowserMockup | placeholder chart; "$45,200"→€; no sidebar; empty bottom
030 | CrmCardSlide | "150 000 ₽" → €
036 | FigureCard | "0 благодати" → "О благодати"; real photo/empty-state
045 | HistoricalCompare | broken images → real assets
047 | InfographicCards | only 3 cards → 4; 3rd card missing icon
082 | ProcessFunnel | only 3 stages → 4
083 | ProductCard | "$49/mo","$199/mo" → €
084 | ProgressScalesSlide | placeholder "Показатель 1/2" → ≥3 real metrics
095 | RoiCalculatorSlide | "$" → €
096 | RulerCompare | "0 постройках" → "О постройках"
016 | ChatMockupSlide | dialogue ends on user → end on bot reply; replace baboon photo
```
