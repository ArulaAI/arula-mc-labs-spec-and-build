.PHONY: demo test grade sync validate clean reset sync-local

demo:
	@echo "Forge Prowess — Engineering — Spec to Trusted Build (Java)"
	@echo "Open LAB_ACTION_GUIDE.md to begin."

test:
	mvn test

# The lab grader is a Python package rooted in the central primitives repo (it imports
# primitives._llm etc.), so it runs with that repo on PYTHONPATH. Deps: pyyaml, pydantic, httpx.
# Override FORGE_PRIMITIVES / PYTHON if your paths differ.
FORGE_PRIMITIVES ?= ../forge-prowess-primitives
PYTHON ?= python3
grade:
	mvn test
	@if [ -d "$(FORGE_PRIMITIVES)/primitives" ]; then \
		PYTHONPATH="$(FORGE_PRIMITIVES)" $(PYTHON) -m primitives.lab_grader.shared.grader . ; \
	else \
		echo "make grade: central primitives package not found at $(FORGE_PRIMITIVES)."; \
		echo "  Set FORGE_PRIMITIVES=/path/to/forge-prowess-primitives and ensure pyyaml/pydantic/httpx are installed."; \
	fi

# The 'forge' CLI is not assumed present (matches the reference lab's convention). 'make sync'
# copies the L2 universal primitives from the central primitives repo if it is available locally.
sync:
	@if command -v forge >/dev/null 2>&1; then \
		forge sync . ; \
	elif [ -d "$(FORGE_PRIMITIVES)/primitives" ]; then \
		echo "forge CLI absent — copying primitives from $(FORGE_PRIMITIVES)"; \
		mkdir -p .forge/primitives; \
		cp -R "$(FORGE_PRIMITIVES)"/primitives/journey_recorder .forge/primitives/; \
		cp -R "$(FORGE_PRIMITIVES)"/primitives/lab_grader .forge/primitives/; \
		cp -R "$(FORGE_PRIMITIVES)"/primitives/journey_curator .forge/primitives/; \
		cp -R "$(FORGE_PRIMITIVES)"/primitives/failure_mode_audit .forge/primitives/; \
	else \
		echo "No forge CLI and no local primitives repo at $(FORGE_PRIMITIVES); primitives already vendored in .forge/primitives/"; \
	fi

# Wire the lab-local primitives (spec-craft, work-orchestrator) into the Claude Code harness.
sync-local:
	cp .forge/local/primitives/spec-craft/adapters/claude_code/SKILL.md \
	   .claude/commands/spec.md
	cp .forge/local/primitives/work-orchestrator/adapters/claude_code/SKILL.md \
	   .claude/commands/build.md
	@echo "spec-craft and work-orchestrator wired into .claude/commands/"

validate:
	@if command -v forge >/dev/null 2>&1; then forge validate . ; else \
		echo "forge CLI absent — checking required files exist"; \
		test -f .forge/manifest.yaml \
		&& echo "OK: .forge manifest present" || (echo "MISSING required .forge files" && exit 1); \
	fi

clean:
	mvn clean
	rm -rf .forge/journey/*.jsonl .forge/.current-run-id

reset:
	git checkout -- src specs exercises docs/workflow-tracker.md
	rm -rf .forge/journey/*.jsonl .forge/.current-run-id target
	@echo "Reset to clean lab baseline."
