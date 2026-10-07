.PHONY: help install test lint lint_format ai_box ai_box_build

help:
	@echo "make install      - install both packages and the dev tools with uv"
	@echo "make test         - run the tests with coverage"
	@echo "make lint         - check formatting, lint and types"
	@echo "make lint_format  - format and auto-fix"
	@echo "make ai_box_build - build the disposable Claude dev box image"
	@echo "make ai_box       - start the box; AIBOX_BRANCH / AIBOX_MCP_BRANCH pick the branches"

install:
	uv sync --all-packages

test: install
	uv run pytest --strict-markers --junitxml=test-results.xml --cov --cov-report=xml --cov-report=html

lint: install
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy -p wflow_api -p wflow_cli

lint_format: install
	uv run ruff format .
	uv run ruff check --fix .

AIBOX_IMAGE ?= wflow-cli-aibox
AIBOX_BRANCH ?= develop
AIBOX_MCP_BRANCH ?= develop

ai_box_build:
	DOCKER_BUILDKIT=1 docker build -f Dockerfile.aibox \
		--build-arg GIT_USER_NAME="$$(git config user.name)" \
		--build-arg GIT_USER_EMAIL="$$(git config user.email)" \
		-t $(AIBOX_IMAGE) .

# Only the Claude config the box needs is staged; the jq filter is duplicated in Dockerfile.aibox.
ai_box: ai_box_build
	@test -n "$$GITHUB_WFLOW_PAT" || { echo "GITHUB_WFLOW_PAT is not set"; exit 1; }
	@mkdir -p docs
	@stage=$$(mktemp -d) && trap 'rm -rf "$$stage"' EXIT INT TERM && \
	for item in CLAUDE.md skills plugins agents; do \
		if [ -e "$$HOME/.claude/$$item" ]; then cp -a "$$HOME/.claude/$$item" "$$stage/"; fi; \
	done && \
	for f in "$$HOME"/.claude/*.sh; do \
		if [ -f "$$f" ]; then cp -a "$$f" "$$stage/"; fi; \
	done && \
	if [ -f "$$HOME/.claude/settings.json" ]; then \
		jq '{enabledPlugins, extraKnownMarketplaces, model, effortLevel, statusLine} | with_entries(select(.value != null))' \
			"$$HOME/.claude/settings.json" > "$$stage/settings.json"; \
	fi && \
	docker run --rm -it \
		--init --pids-limit 512 --memory 8g --cpus 4 --cap-drop=ALL --security-opt no-new-privileges \
		-e GITHUB_WFLOW_PAT \
		-e AIBOX_BRANCH="$(AIBOX_BRANCH)" \
		-e AIBOX_MCP_BRANCH="$(AIBOX_MCP_BRANCH)" \
		-v "$$stage:/host-claude:ro" \
		-v "$(CURDIR)/docs:/home/dev/docs:rw" \
		$(AIBOX_IMAGE)
