# AI-Assisted Game Development Studio — Roadmap

## Strategic Context

**Market gap identified**: ComfyUI (deepest node graph) and InvokeAI (best canvas UX) are powerful general AI image tools, but neither is game-aware. SEELE AI and Pixel Asset Forge are game-focused but cloud-only and shallow. **No existing tool** combines local inference, game-specific asset workflows, professional node graphs, and studio-grade asset management.

**Core differentiator**: This is not "another AI image generator." It is a **professional game development tool** powered by AI — the Blender of AI-assisted game asset creation.

**Architecture decision**: Tauri 2.0 + Python sidecar + TypeScript frontend. WebGL-accelerated node graph (XenolithGraph-class). Plugin system modeled on ComfyUI's `entry_points` + `WEB_DIRECTORY` pattern. Projects stored as AIFP-compatible ZIP containers. Asset metadata in PNG chunks + SQLite catalog.

---

## Phase 0 — Foundation (Months 1-3)

**Theme**: "Build the pipe, not the game." Get a single image from prompt-to-screen with full reproducibility.

### Milestone 0.1: Scaffold & Architecture (Week 1-2)
- [ ] Tauri 2.0 shell with Vue 3 + TypeScript frontend
- [ ] Python sidecar spawning via sidecar API (bundled python-build-standalone)
- [ ] IPC bridge (Tauri commands ↔ FastAPI/WebSocket)
- [ ] GPU detection: `gpu-doctor` integrated — detect CUDA/ROCm/DirectML/Metal
- [ ] CI matrix: Windows (CUDA, DirectML), Linux (CUDA, ROCm), macOS (MPS)
- [ ] Auto-download correct PyTorch environment on first launch

### Milestone 0.2: Abstraction Layer (Week 3-5)
- [ ] Backend interface: `GenerationBackend` abstract class
  ```python
  class GenerationBackend(ABC):
      async def generate(self, params: GenParams) -> GenerationResult: ...
      async def list_models(self) -> list[ModelInfo]: ...
      async def load_model(self, model_id: str) -> bool: ...
      async def unload_all(self): ...
  ```
- [ ] ComfyUI backend adapter (wraps ComfyUI as library or subprocess)
- [ ] Diffusers backend adapter (native PyTorch, no ComfyUI dep)
- [ ] Backend auto-selection (ComfyUI preferred if installed, else diffusers)
- [ ] VRAM-aware model management (load/unload on demand, `--lowvram` equivalency)
- [ ] Background queue: `asyncio.Queue` + worker coroutine with WebSocket progress streaming

### Milestone 0.3: Plugin System (Week 6-8)
- [ ] Plugin discovery via `entry_points` + filesystem scan (`plugins/` directory)
- [ ] Plugin lifecycle: discover → validate deps → import → register
- [ ] Frontend plugin hooks: custom panels, toolbar items, context menu entries
- [ ] Plugin dependency management (pip subprocess in isolated venv)
- [ ] Plugin marketplace schema (manifest, version, compatibility)
- [ ] Example plugin: "Simple LoRA Stacker"
- [ ] Plugin sandboxing (process isolation for untrusted plugins)

### Milestone 0.4: Asset Storage & Reproducibility (Week 9-10)
- [ ] Image generation with full metadata: prompt, seed, model, LoRAs, ControlNets, date, graph snapshot
- [ ] Metadata embedded in PNG `tEXt` chunks (compatible with A1111/ComfyUI standards)
- [ ] SQLite asset catalog: tags, ratings, relationships, version history
- [ ] Project file format: AIFP-based ZIP container with `manifest.json`, assets, workflows
- [ ] Sidecar `.meta` JSON for lossy formats (JPEG, WebP)
- [ ] Asset import from ComfyUI/InvokeAI/A1111 (parse their metadata formats)

### Milestone 0.5: Basic Generation UI (Week 11-12)
- [ ] Prompt input with negative prompt field
- [ ] Model selector (populated from backend + model manager)
- [ ] Seed control (random/fixed, recent seeds list)
- [ ] Generation parameters panel: CFG, steps, scheduler, sampler, resolution
- [ ] Live progress display (WebSocket stream)
- [ ] Gallery grid with thumbnail view
- [ ] Click to view full metadata
- [ ] Regenerate with same seed
- [ ] Save to project
- [ ] Dark mode, dockable panels (GoldenLayout or similar)

**DONE: Phase 0 — You can generate, save, and reproduce an image with full metadata.**

---

## Phase 1 — Model & Prompt Ecosystem (Months 4-6)

**Theme**: "Make the toolbox professional." Model management, prompt studio, batch workflows.

### Milestone 1.1: Model Manager (Week 13-15)
- [ ] Auto-scan checkpoints, LoRAs, VAEs, embeddings, ControlNets from:
  - Local folders (configurable, multiple paths)
  - HuggingFace cache (`~/.cache/huggingface`)
  - CivitAI downloads folder
- [ ] Model metadata parsing (CivitAI info, HF model cards, safetensors headers)
- [ ] Model preview thumbnails
- [ ] Model tagging and filtering (type, base model, size, trigger words)
- [ ] Symbolic link / copy management for model organization
- [ ] Model downloader (HF hub, CivitAI API)
- [ ] Model versioning (track which version generated which asset)

### Milestone 1.2: Prompt Studio (Week 16-18)
- [ ] Rich text editor with syntax highlighting for prompt tokens
- [ ] Prompt templates: `{character} in {setting}, wearing {outfit}`
- [ ] Wildcard system: `__color__`, `__weapon__` with weighted random selection
- [ ] Reusable snippet library (save/share prompt fragments)
- [ ] Prompt variables (per-project, per-generation)
- [ ] Prompt history (full text, searchable, filterable)
- [ ] Side-by-side prompt comparison (A/B test prompts)
- [ ] Prompt ratings (save favorites, hide failures)
- [ ] Semantic prompt search via embeddings
- [ ] Prompt versioning (track changes over time)

### Milestone 1.3: Batch & Queue (Week 19-21)
- [ ] Batch generation: N images with same params, varying seeds
- [ ] Parameter grid: sweep over seeds, CFG, steps, LoRA weights
  - Example: 4 seeds × 3 CFG values × 2 LoRA weights = 24 images
- [ ] Queue system: reorder, prioritize, cancel, pause/resume
- [ ] Queue presets: "Quick exploration" (4 images), "Production" (16+)
- [ ] Background generation (continue working while queue runs)
- [ ] Completion notifications (system toast / sound)
- [ ] Queue history with results summary

### Milestone 1.4: Reproducibility Deepening (Week 22-24)
- [ ] Graph snapshot: every generation saves its full pipeline as a graph JSON
- [ ] "Open in node graph" button on any generated image
- [ ] Full pipeline comparison between two generations
- [ ] Deterministic mode: fixed seeds, fixed graph → identical output across runs
- [ ] Regression testing: golden image comparison for pipeline validation

**DONE: Phase 1 — Professional prompt workflow with full model management.**

---

## Phase 2 — Core Game Asset Pipelines (Months 7-10)

**Theme**: "Generate game assets, not just pictures." Game-aware generation modules.

### Milestone 2.1: Character Generator (Week 25-28)
- [ ] Multi-view generation: front, back, side, 3/4 in one batch
- [ ] Expression sheet: happy, sad, angry, surprised, idle, etc.
- [ ] Equipment variants UI: generate character with different weapons/armor
- [ ] Color variant batch: same pose, different palette
- [ ] Hair/clothing variant batch
- [ ] Pose library: idle, walk, attack, cast, death, damage
- [ ] Animation sheet export: grid of poses for sprite slicing
- [ ] Character consistency via:
  - IP-Adapter face/armor reference
  - LoRA stacking for character elements
  - ControlNet pose conditioning

### Milestone 2.2: Sprite Sheet Generator (Week 29-32)
- [ ] Animation frame sequence generator
- [ ] Idle → Walk → Run → Jump → Attack → Cast → Death → Damage
- [ ] Directional variants: 4-direction, 8-direction
- [ ] Frame interpolation between keyframes
- [ ] Pixel-perfect alignment across frames
- [ ] Automatic sprite packing (optimal atlas layout)
- [ ] Sprite sheet metadata export (JSON with frame rects, pivot points)
- [ ] Export targets: PNG spritesheet + JSON, Aseprite, individual frames
- [ ] Onion-skinning preview for frame consistency

### Milestone 2.3: Tileset Generator (Week 33-36)
- [ ] Tile size presets: 16×16, 32×32, 48×48, 64×64, 128×128
- [ ] Autotile generation (auto-detecting corner/edge/center tiles)
- [ ] Terrain transition tiles (grass→dirt, sand→water, etc.)
- [ ] Road/Path generation with junctions
- [ ] Water animation tiles (shore, waves, deep)
- [ ] Cliff/wall tilesets with seamless vertical tiling
- [ ] Building/roof tilesets
- [ ] Dungeon tiles (walls, floors, doors, traps)
- [ ] Vegetation/object/decorative tiles
- [ ] Seamless tile checking (visual overlay for seams)
- [ ] Palette locking across tileset

### Milestone 2.4: Battle Map Generator (Week 37-40)
- [ ] Map type presets: fantasy, cyberpunk, sci-fi, post-apocalyptic
- [ ] Environment: indoor, outdoor, caves, cities, forests, dungeons
- [ ] Grid generation: square grid, hex grid
- [ ] Auto-populate: enemies, objects, terrain features
- [ ] Lighting regions (day/night, dungeon darkness)
- [ ] Fog of war layers
- [ ] Object layers: chests, doors, traps, interactables
- [ ] Editable regions (click to regenerate individual map sections)
- [ ] D&D encounter map presets
- [ ] Export to: PNG, Tiled `.tmx`, VTT (Foundry, Roll20)

**DONE: Phase 2 — Core game asset types are generatable.**

---

## Phase 3 — Professional Tooling (Months 11-14)

**Theme**: "Expert control surfaces." Node graph, pose studio, canvas, AI-assisted editing.

### Milestone 3.1: Visual Node Graph (Week 41-46)
- [ ] WebGL-accelerated node editor (XenolithGraph or canvas-harness based)
- [ ] Core node library:
  - Model loading (checkpoint, LoRA, VAE, ControlNet)
  - Prompt manipulation (concat, wildcard expand, template fill)
  - Image preprocessing (resize, crop, mask, blur)
  - ControlNet chaining (Canny, Depth, OpenPose, Scribble, etc.)
  - Postprocessing (upscale, tile, background remove)
  - IP-Adapter nodes
  - Mask/blend operations
- [ ] Node categories with search
- [ ] Macro system: group nodes into reusable macro
- [ ] Custom Python node support (write inline Python in node)
- [ ] Node graph import/export as JSON
- [ ] Graph versioning with diff view
- [ ] Partial graph execution (run only selected nodes)
- [ ] Node execution status visualization (pending → running → done → error)
- [ ] Real-time preview nodes (see output at any point in pipeline)

### Milestone 3.2: Pose Studio (Week 47-50)
- [ ] 2D skeleton editor with bone hierarchy
- [ ] Bone manipulation: rotate, translate, scale with IK/FK
- [ ] Import pose from reference image (OpenPose extraction)
- [ ] Pose library: save/load poses, search by name/tag
- [ ] Pose blend between two poses (animation keyframe concept)
- [ ] Pose → ControlNet conditioning (OpenPose skeleton render)
- [ ] Manual pose correction (edit detected skeleton from image)
- [ ] Multi-character pose editing (scene composition)

### Milestone 3.3: Interactive Canvas (Week 51-54)
- [ ] Infinite canvas with pan/zoom
- [ ] Drag-drop images from gallery onto canvas
- [ ] Inpaint canvas region (select area → repaint)
- [ ] Outpaint (expand canvas in any direction)
- [ ] Remove object (brush-select → remove)
- [ ] Replace clothing/background (lasso-select → replace with prompt)
- [ ] Change lighting/weather/season across canvas
- [ ] Image comparison: side-by-side, swipe, difference overlay
- [ ] Version tree: see generation lineage (original → inpaint variant → upscale)
- [ ] Annotations: text notes, arrows, highlights on canvas
- [ ] Bookmarks: named canvas locations for quick navigation
- [ ] Collections: organize canvas items into groups
- [ ] Mood board layout: grid, freeform, storyboard

### Milestone 3.4: AI-Assisted Editing (Week 55-56)
- [ ] Inpainting (mask → regenerate)
- [ ] Outpainting (extend canvas)
- [ ] Expand canvas with content-aware fill
- [ ] Style transfer (apply reference style to existing asset)
- [ ] Expression editing (change character expression)
- [ ] Age variants (make character older/younger)
- [ ] Damage/weather variants (clean → damaged → weathered)
- [ ] Recolor with palette lock
- [ ] Upscaling (ESRGAN, 4x, 8x)
- [ ] Background removal (RMBG, rembg)
- [ ] Tiled/Seamless conversion

**DONE: Phase 3 — Professional editing with node graph and canvas.**

---

## Phase 4 — Intelligence & Consistency (Months 15-17)

**Theme**: "The tool remembers." Style memory, auto-relationships, asset database intelligence.

### Milestone 4.1: Style Memory (Week 57-60)
- [ ] Style signature extraction: given a reference image, extract:
  - Color palette (quantized 16-32 color palette)
  - Lighting profile (direction, intensity, warmth)
  - Line art style (thickness, softness, texture)
  - Rendering style (cel-shaded, painted, pixel, realistic)
- [ ] Style matching: given a new prompt, find best reference style from library
- [ ] Style enforcement: IP-Adapter + prompt engineering to enforce extracted style
- [ ] Cross-asset style consistency:
  1. User generates "Knight A"
  2. System extracts style signature
  3. User generates "Knight A's shield"
  4. System automatically conditions with extracted style
- [ ] Style library: saved style signatures with previews
- [ ] Style blend: interpolate between two styles
- [ ] Style override: force any asset to match selected style

### Milestone 4.2: Auto Asset Relationships (Week 61-63)
- [ ] If a character exists, auto-generate:
  - Portrait (headshot)
  - Bust (shoulders up)
  - Full sprite (full body)
  - Dialogue portrait (game-ready)
  - Combat token (top-down)
  - Inventory icon
  - Paper doll segments
  - Animation sheet link
- [ ] Relationship graph visualization
- [ ] Dependency tracking: if character is regenerated, mark dependent assets as stale
- [ ] Batch regenerate dependent assets when source changes
- [ ] Smart default generation parameters per asset type

### Milestone 4.3: Asset Database Intelligence (Week 64-66)
- [ ] Full-text search across prompts, tags, filenames, metadata
- [ ] Semantic search (embedding-based similarity)
- [ ] Visual similarity search (image embedding comparison)
- [ ] Asset clustering: "show me all knight-type assets"
- [ ] Usage tracking: "which assets are unused? which are most used?"
- [ ] Style consistency scoring: "how well does this match the project style?"
- [ ] Duplicate detection (perceptual hashing)
- [ ] Missing asset detection: "this character has no portrait"
- [ ] Batch metadata editor
- [ ] Advanced filtering: by model, seed range, date, rating, tags

### Milestone 4.4: AI Assistant Integration (Week 67-68)
- [ ] Assistant understands current project context
- [ ] Can recommend:
  - LoRAs for current character style
  - Prompt improvements ("try adding 'dramatic lighting'")
  - Better ControlNet configuration
  - Upscaling strategy based on asset type
  - Animation workflow suggestions
- [ ] "What should I generate next?" based on missing assets
- [ ] Style consistency warnings ("this asset doesn't match project style")
- [ ] Assistant accessible from context menu on any asset

**DONE: Phase 4 — The system learns and maintains consistency.**

---

## Phase 5 — Platform & Ecosystem (Months 18-21)

**Theme**: "Ship to engines, share with teams." Exporters, marketplace, documentation.

### Milestone 5.1: Exporters (Week 69-73)
- [ ] Unity: `.png` + `.meta`, sprite sheet import, tile palette
- [ ] Godot: `.png` + `.import`, sprite sheet, tileset scene
- [ ] Unreal: `.png` + paper2D sprite setup, texture import
- [ ] RPG Maker: character sheets, tilesets in format-specific layout
- [ ] Construct: sprite sheets with JSON
- [ ] GameMaker: sprite strip with `.yy` data
- [ ] GDevelop: sprite resources
- [ ] Ren'Py: sprite, background, GUI elements
- [ ] Generic: PNG sequence, spritesheet + JSON, Aseprite `.ase`, PSD layers
- [ ] Tiled: `.tsx` tileset files, `.tmx` map files
- [ ] SVG vector trace for UI elements
- [ ] Export presets with per-engine optimization

### Milestone 5.2: Project System (Week 74-76)
- [ ] Project creation wizard
- [ ] Project templates: "2D RPG", "Platformer", "Top-down Shooter", "Blank"
- [ ] Project-wide settings: default resolution, style, naming conventions
- [ ] Asset organization within projects (folders, collections)
- [ ] Project sharing: export/import full project as `.aifp`
- [ ] Multi-user project support (file-based, later git-aware)
- [ ] Project analytics: asset count, storage usage, generation stats
- [ ] Autosave with history

### Milestone 5.3: Marketplace (Week 77-79)
- [ ] In-app marketplace browser
- [ ] Shared content types:
  - Node graphs (reusable generation pipelines)
  - Prompt packs (themed collections)
  - Style signatures
  - LoRAs (with CivitAI integration)
  - Macros (reusable node graph snippets)
  - Templates (project templates)
  - Plugins
- [ ] One-click install to project
- [ ] Rating/review system
- [ ] Creator profiles

### Milestone 5.4: Extensibility API (Week 80-82)
- [ ] Python API: full access to generation, asset DB, project system
- [ ] REST API: headless operation for CI/CD pipelines
- [ ] Plugin SDK: documentation, examples, template
- [ ] CLI: `meshdewarper generate --prompt "..." --seed 42 --output knight.png`
- [ ] WebSocket API: real-time generation streaming
- [ ] Automation hooks: "on generation complete", "on asset import", etc.

### Milestone 5.5: CI/CD & Packaging (Week 83-84)
- [ ] GitHub Actions: automated testing, linting, type checking
- [ ] Nightly builds for all platforms
- [ ] Cross-platform installer:
  - Windows: NSIS/Inno Setup installer
  - Linux: AppImage + .deb + .rpm
  - macOS: .dmg
- [ ] Auto-updater (Tauri updater)
- [ ] Crash reporting (opt-in)
- [ ] Telemetry (opt-in, minimal: hardware, version, feature usage)

### Milestone 5.6: Documentation (Week 85-88)
- [ ] Architecture diagrams (C4 model)
- [ ] API reference (auto-generated from Python + TypeScript)
- [ ] Developer guide: how to write plugins, custom nodes
- [ ] User manual: workflow-based tutorials
- [ ] Plugin developer guide
- [ ] Contribution guide
- [ ] Example workflows: "Generate a complete RPG character in 10 minutes"
- [ ] Tutorial projects: "Build a fantasy tileset from scratch"
- [ ] Video walkthroughs (links to external)

**DONE: Phase 5 — Professional platform with engine integration.**

---

## Phase 6 — Advanced & Future (Months 22-24+)

**Theme**: "Push boundaries." Next-gen AI, 3D, animation, audio.

### Milestone 6.1: Video & Animation (Month 22-23)
- [ ] AnimateDiff integration for animation generation
- [ ] Keyframe animation with interpolation
- [ ] Motion LoRAs
- [ ] Video-to-video style transfer
- [ ] Animation preview player
- [ ] Export as GIF, MP4, spritesheet, PNG sequence
- [ ] Rigging support (2D skeleton → AI-generated animation)
- [ ] Motion capture import (video → skeleton → animation)

### Milestone 6.2: 3D Asset Generation (Month 23-24)
- [ ] Text-to-3D (via Gaussian Splatting, Mesh Diffusion, or similar)
- [ ] Image-to-3D
- [ ] PBR texture generation (albedo, normal, roughness, AO, height, metalness)
- [ ] 3D model preview (WebGL viewer in app)
- [ ] 3D asset export (glTF, FBX, OBJ)
- [ ] Voxel generation (MagicaVoxel format)
- [ ] Material generation (Substance-style layered materials)

### Milestone 6.3: Audio & Dialogue (Beyond 24 months)
- [ ] AI SFX generation (footsteps, impacts, ambient)
- [ ] Music generation (looping tracks, themes)
- [ ] NPC dialogue generation (with voice)
- [ ] Voice variant generation (different accents, emotions)
- [ ] Audio asset management in project system

### Milestone 6.4: Complete Game Prototyping (Beyond 24 months)
- [ ] "Generate a game from description" (code + assets)
- [ ] Procedural level generation with AI
- [ ] Quest generation
- [ ] NPC behavior generation
- [ ] Dialogue tree generation
- [ ] Integration with Godot/Unity via plugins for real-time generation

### Milestone 6.5: Future-Proof Architecture (Ongoing)
- [ ] SD4 support when released
- [ ] Diffusion Transformer support (SD3, FLUX, etc.)
- [ ] Multi-modal model support
- [ ] Voice-controlled generation
- [ ] NPU acceleration (Apple Neural Engine, Qualcomm, Ryzen AI)
- [ ] Cloud hybrid mode (optional, for when local GPU is insufficient)

**DONE: Phase 6 — Full multimedia game asset pipeline.**

---

## Key Design Principles (Recurring)

1. **Reproducibility first**: Every asset stores full generation provenance. No black boxes.
2. **Local by default**: Zero cloud dependency. Everything runs on user hardware.
3. **Plugin everything**: Core is minimal. Features are plugins. Community extends.
4. **Game-aware, not game-specific**: Tilesets know they tile. Sprites know their frames. Characters know their poses.
5. **Progressive disclosure**: Beginners see prompt + generate. Experts go to node graph.
6. **Style as data**: Style is extractable, savable, transferable, and enforceable — not accidental.
7. **Deterministic when desired**: Same pipeline → same output. Regression-testable.
8. **Human in the loop**: Every generation is editable, refinable, rejectable. AI proposes, human disposes.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| GPU fragmentation (ROCm/DirectML bugs) | High | High | Extensive CI testing per platform, graceful CPU fallback, community issue tracker |
| Python dependency hell | High | Medium | python-build-standalone with pinned deps, pre-built env archives, Docker-based CI |
| Plugin security (malicious code execution) | Medium | High | Process isolation for untrusted plugins, manifest-based permissions, sandboxed execution |
| Model licensing (LoRAs, checkpoints) | Low | Medium | Clear licensing display, filter by commercial-use, user responsibility disclaimer |
| Scope creep | High | High | Strict phase gating, no Phase N+1 until Phase N is complete and stable |
| Community node compatibility (ComfyUI) | Medium | Medium | Adapter pattern, version-pin ComfyUI dependency, compatibility matrix |
| Performance on low-end GPUs | Medium | Medium | VRAM budgeting, model offloading, CPU fallback with progressive degradation |

---

## Measuring Success

- **Phase 0**: User can install, generate an image, find it in gallery, reproduce it. < 5 minutes from install to first image.
- **Phase 1**: Power user can create prompt templates, sweep parameters, manage 100+ models.
- **Phase 2**: Solo dev generates a complete 2D RPG character (8 poses, 4 directions) in < 1 hour.
- **Phase 3**: Artist builds a custom node graph with ControlNet chaining and saves it as a reusable macro.
- **Phase 4**: User generates 50+ assets that look like they belong to the same game without manual style tuning.
- **Phase 5**: Studio exports to Godot/Unity, shares project with team, publishes a plugin.
- **Phase 6**: Complete game prototype (3 rooms, 2 characters, 10 items, 3 enemies) generated in < 1 day.
