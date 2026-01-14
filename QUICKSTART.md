# PaperGen Quick Start Cheat Sheet

## Installation (One-Time Setup)

```bash
# 1. Install
cd /path/to/academic-paper-pipeline
pip install -e .

# 2. Set API key
export ANTHROPIC_API_KEY='your-key-here'
# Get your key at: https://console.anthropic.com/

# 3. Verify
papergen --help
```

---

## Using Custom API Endpoints (Optional)

PaperGen supports self-hosted Anthropic API and third-party providers like LiteLLM, OpenRouter, etc.

```bash
# Option 1: Environment variable
export ANTHROPIC_BASE_URL='https://your-api-endpoint.com/v1'
export ANTHROPIC_API_KEY='your-key-here'

# Option 2: Config file (edit config/default_config.yaml)
# api:
#   base_url: https://your-api-endpoint.com/v1

# Examples:
# LiteLLM: export ANTHROPIC_BASE_URL='https://your-litellm-proxy.com'
# OpenRouter: export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'
```

**Note:** Leave `ANTHROPIC_BASE_URL` unset to use the default Anthropic API.

---

## Write Your First Paper (5 Minutes)

```bash
# Step 1: Create project (30 seconds)
mkdir my-paper && cd my-paper
papergen init "My Research Topic" --template ieee --author "Your Name"

# Step 2: Add research (1 minute)
papergen research add paper1.pdf paper2.pdf
papergen research add notes.md --source-type note
papergen research organize

# Step 3: Create outline (30 seconds)
papergen outline generate
papergen outline show

# Step 4: Draft paper (2 minutes - AI writes everything!)
papergen draft all

# Step 5: Review and revise (1 minute)
papergen draft review introduction
papergen revise revise-section introduction --feedback "Add more recent work"

# Step 6: Generate PDF (30 seconds)
papergen format latex
papergen format compile --open

# Done! 🎉
```

---

## Essential Commands

### Project Setup
```bash
papergen init "Topic"              # Start new project
papergen status                    # Check progress
```

### Research
```bash
papergen research add *.pdf        # Add PDFs
papergen research add --url URL    # Add from web
papergen research organize         # AI organizes everything
papergen research list             # See all sources
```

### Outline
```bash
papergen outline generate          # Create outline
papergen outline show              # View outline
papergen outline refine            # Edit interactively
```

### Drafting
```bash
papergen draft draft-section NAME  # Draft one section
papergen draft all                 # Draft everything
papergen draft show NAME           # View draft
papergen draft list                # List all drafts
papergen draft stats               # See statistics
```

### Revision
```bash
papergen draft review NAME                    # Get AI review
papergen revise revise-section NAME --feedback "..."  # Major revision
papergen revise polish NAME --focus clarity   # Minor polish
papergen revise all --feedback "..."          # Revise all sections
papergen revise history NAME                  # See version history
papergen revise compare NAME                  # Compare versions
papergen revise revert NAME 1                 # Go back to version 1
```

### Formatting
```bash
papergen format latex --template ieee    # Generate LaTeX
papergen format markdown                 # Generate Markdown
papergen format compile                  # Create PDF
papergen format compile --open           # Create and open PDF
```

### Research Discovery (For Students)
```bash
papergen discover survey paper.pdf -t "NLP"   # Analyze survey paper
papergen discover paper paper.pdf             # Deep analyze a paper
papergen discover brainstorm "topic" -n 5     # Generate research ideas
papergen discover brainstorm "topic" -m       # Multi-LLM brainstorming
```

---

## Common Workflows

### Quick Draft
```bash
papergen init "Topic"
papergen research add *.pdf && papergen research organize
papergen outline generate && papergen draft all
papergen format latex && papergen format compile --open
```

### High-Quality Paper
```bash
# After drafting...
for section in introduction methods results conclusion; do
  papergen draft review $section
  papergen revise revise-section $section --interactive
  papergen revise polish $section --focus clarity
  papergen revise polish $section --focus citations
done
papergen format latex && papergen format compile --open
```

### Add More Research
```bash
papergen research add new_papers/*.pdf
papergen research organize          # Re-organize with new sources
papergen draft draft-section intro  # Re-draft affected sections
```

### Postgraduate Student Workflow (From Abstract Topic to Paper Idea)
```bash
# Step 1: Your supervisor gives you a broad topic like "NLP" or "LLM"
# Download a recent survey paper from arXiv

# Step 2: Analyze the survey to understand the research landscape
papergen discover survey survey_paper.pdf -t "Large Language Models" -o landscape.json

# Step 3: Identify critical papers for deep reading
# The survey analysis will list key papers to read

# Step 4: Deep analyze 2-3 critical papers
papergen discover paper critical_paper1.pdf
papergen discover paper critical_paper2.pdf

# Step 5: Brainstorm novel research ideas based on gaps and weaknesses
papergen discover brainstorm "LLM efficiency" -n 5 -c landscape.json

# Step 6: Pick the best idea and start writing!
papergen init "Your Novel Idea Title" --template acl
```

### Multi-LLM Brainstorming (Recommended)
```bash
# Set up multiple API keys
export ANTHROPIC_API_KEY='your-claude-key'
export OPENAI_API_KEY='your-openai-key'
export GEMINI_API_KEY='your-gemini-key'

# Run multi-LLM brainstorming
papergen discover brainstorm "topic" -m -n 5 -o ./brainstorm_results

# This will:
# 1. Generate ideas from all configured LLMs in parallel
# 2. Summarize and deduplicate ideas using Claude
# 3. Save individual reports and summary to output directory
```

---

## Troubleshooting Quick Fixes

### "API key not found"
```bash
export ANTHROPIC_API_KEY='your-key'
# or
echo "ANTHROPIC_API_KEY=your-key" > .env
```

### "Not in a papergen project"
```bash
cd /path/to/your/paper  # Make sure you're in project directory
ls .papergen            # Should exist
```

### "LaTeX compilation failed"
```bash
# Install LaTeX:
# macOS:   brew install --cask mactex
# Ubuntu:  sudo apt-get install texlive-full
# Windows: Download MiKTeX from miktex.org
```

### Draft quality is poor
```bash
# Add better sources
papergen research add high_quality_papers/*.pdf
papergen research organize --focus "methodology, results"

# Use specific guidance
papergen draft draft-section intro \
  --guidance "Focus on novelty. Cite papers from 2023-2024."

# Give detailed feedback
papergen revise revise-section intro \
  --feedback "Add 3 specific examples. Cite Smith2024. Emphasize climate urgency."
```

---

## Tips

1. **Add 5-10 good papers** for best results
2. **Use `--focus`** when organizing research
3. **Give specific feedback** when revising
4. **Polish critical sections** (abstract, intro, conclusion)
5. **Check status often**: `papergen status`
6. **View logs for debugging**: `papergen --debug COMMAND`
7. **Manual edits allowed**: Edit `drafts/*.md` directly
8. **Use git** for version control
9. **Iterate freely** - all versions are saved!
10. **Read LEARN.md** for detailed explanations

---

## Templates

### NLP Conferences (ACL/EMNLP/NAACL)
```bash
papergen init "Topic" --template acl
papergen format latex --template acl
```

### AAAI
```bash
papergen init "Topic" --template aaai
papergen format latex --template aaai
```

### IJCAI
```bash
papergen init "Topic" --template ijcai
papergen format latex --template ijcai
```

### NeurIPS
```bash
papergen init "Topic" --template neurips
papergen format latex --template neurips
```

### ICML
```bash
papergen init "Topic" --template icml
papergen format latex --template icml
```

### IEEE (Conference)
```bash
papergen init "Topic" --template ieee
papergen format latex --template ieee
```

### ACM (Conference)
```bash
papergen init "Topic" --template acm
papergen format latex --template acm
```

### Markdown (arXiv/Blog)
```bash
papergen format markdown --template arxiv
papergen format markdown --template github
```

---

## Getting Help

```bash
papergen --help                          # General help
papergen research --help                 # Research commands
papergen draft draft-section --help      # Specific command help
```

**Documentation:**
- `LEARN.md` - Complete beginner's guide
- `docs/getting_started.md` - Tutorial
- `docs/commands.md` - Full command reference
- `docs/workflow.md` - Real-world examples
- `docs/troubleshooting.md` - Detailed fixes

---

## Example: Complete Paper in 5 Commands

```bash
mkdir paper && cd paper
papergen init "AI for Climate" --template ieee --author "Me"
papergen research add ~/papers/*.pdf && papergen research organize
papergen outline generate && papergen draft all
papergen format latex && papergen format compile --open
```

**That's it! Happy writing! 🚀**
