# CodeCompanion Strength Coach - Quick Reference Guide

## Keymaps

| Keymap | Description | Usage |
|--------|-------------|-------|
| `<leader>cc` | **Coach Chat** | Open interactive coaching chat (default `<space>cc` in LazyVim) |
| `<leader>ce` | **Extend Workout** | **Visual mode only**: Select workout text, then press to extend it 4 weeks |
| `<leader>cg` | **Generate Plan** | Generate a new workout plan from scratch |
| `<leader>cs` | **Switch Strategy** | Switch between coaching methodologies (Rippetoe, Conjugate, etc.) |

**Note**: `<leader>` is usually `<space>` in LazyVim.

## Basic Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `:CodeCompanionChat` | Open the coaching chat | `:CodeCompanionChat` |
| `:CodeCompanion` | Inline assistant (triggers prompt menu) | `:CodeCompanion` (then select prompt) |
| `:CoachStrategy` | Switch coaching strategy | `:CoachStrategy` (shows menu) |

## How to Use It

### 1. **Chat Mode** (for conversation and analysis)
```
<leader>cc    # Opens chat with memories auto-loaded
```

**What you'll see**:
- Your memory files (markup.md, RPE-men-women.md, rip-intensity-chart.md) at the top
- Chat interface ready for coaching questions

**Example questions**:
- "What's the Rippetoe progression for week 2 squats?"
- "How should I adjust this workout based on client feedback?"
- "Explain the markup format for coach notes"

### 2. **Extend Workout** (for programming progression)
```
# Create or open a workout file:
Workout Date: 2025-01-20
Squat
3x5 @ 225
    > Week 1: Starting conservative after layoff
(1x5 @ 225)
(1x5 @ 230)
(1x5 @ 225)

# Select the workout text (visual mode: v, then motion)
# Press <leader>ce
# Choose "Extend workout using current strategy"
# Get 4 more weeks with progression + coach notes
```

### 3. **Generate New Plan**
```
<leader>cg    # Triggers prompt menu
# Choose "Generate new workout plan" 
# It will ask for weeks (default: 4)
# Generates complete program in markup format
```

### 4. **Switch Strategy**
```
:CoachStrategy    # Shows menu:
1. Default: RPE + Rippetoe Linear Progression
2. Conjugate Method (Louie Simmons)  
3. Block Periodization
4. High-Low-Medium Method

# Pick one - loads appropriate memory files
```

## Workflow Examples

### Example 1: Analyze Client Progress
```
1. <leader>cc                    # Open chat
2. Paste client's workout history
3. Ask: "Analyze this 4-week progression. Should I deload?"
4. Get analysis with recommendations + coach notes
```

### Example 2: Extend Existing Program
```
1. Open client_workout.md
2. Select weeks 1-4 (vgg to select all)
3. <leader>ce                    # Extend workout
4. Choose "extend_workout" prompt
5. Get weeks 5-8 with progression + new coach notes
6. Review and save
```

### Example 3: Create New Client Program
```
1. <leader>cg                    # Generate plan
2. Choose "generate_plan" prompt
3. Enter: "8 weeks for 35yo male, squat PR 315lbs"
4. Get complete 8-week program in markup format
5. Copy to client_workout.md
```

## Memory System

**Auto-loaded files** (when you switch strategies):
- **Default**: `markup.md`, `rip-intensity-chart.md`, `RPE-men-women.md`
- **Conjugate**: All `.md` files in `~/.config/nvim/codecompanion_memories/conjugate/`
- **Block**: All `.md` files in `~/.config/nvim/codecompanion_memories/block_periodization/`
- **HLM**: All `.md` files in `~/.config/nvim/codecompanion_memories/hlm/`

**Files appear** at the top of every chat buffer automatically.

## Prompt Selection

When you use `<leader>ce` or `<leader>cg`, you'll see a **prompt menu**:
- **"Strength coaching chat"** - Basic coaching conversation
- **"Extend workout using current strategy"** - Extend selected workout
- **"Generate new workout plan"** - Create new program

Just use arrow keys or `j/k` to select, then `<Enter>`.

## Quick Start Checklist

- [ ] **Files exist**: `~/.config/nvim/codecompanion_memories/default/` contains `markup.md`, `rip-intensity-chart.md`, `RPE-men-women.md`
- [ ] **Environment**: `export GEMINI_API_KEY="your-key"` in your shell
- [ ] **Test chat**: `<leader>cc` → ask "What's RPE 8 for men?" (should reference RPE-men-women.md)
- [ ] **Test extension**: Create sample workout → select → `<leader>ce` → should extend 4 weeks
- [ ] **Test generation**: `<leader>cg` → should create new plan

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **"No API key" error** | Check `echo $GEMINI_API_KEY` in terminal |
| **No memories in chat** | Verify files exist in `~/.config/nvim/codecompanion_memories/default/` |
| **Programming assistant** | Use `<leader>ce` or `<leader>cg` (inline prompts), not just chat |
| **No prompt menu** | Make sure you're in normal mode when pressing keymaps |
| **Keymaps don't work** | Run `:map <leader>c` to check bindings |

## Pro Tips

1. **Always select text** before `<leader>ce` - it uses your selection as context
2. **Use chat** (`<leader>cc`) for analysis and questions, **inline** (`<leader>ce/cg`) for generating markup
3. **Memories auto-update** - add new `.md` files to strategy folders, they'll load next time you switch
4. **Coach notes** (`> `) are preserved automatically when extending workouts
5. **Copy results** from inline prompts back to your workout files

This should get you up and running quickly! Start with `<leader>cc` to test the chat, then try extending a sample workout with `<leader>ce`.
