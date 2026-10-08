.PHONY: build-EventApiFunction build-InvestigationFunction build-ScoringTriggerFunction

build-EventApiFunction:
	mkdir -p "$(ARTIFACTS_DIR)/backend"
	cp backend/__init__.py "$(ARTIFACTS_DIR)/backend/"
	cp -R backend/api backend/agent backend/common backend/ingestion "$(ARTIFACTS_DIR)/backend/"
	find "$(ARTIFACTS_DIR)" -type d -name __pycache__ -prune -exec rm -rf {} +

build-InvestigationFunction:
	mkdir -p "$(ARTIFACTS_DIR)/backend"
	python -m pip install --disable-pip-version-check --no-deps strands-agents==1.58.1 -t "$(ARTIFACTS_DIR)"
	python -m pip install --disable-pip-version-check -r infrastructure/sam/agent-requirements.txt -t "$(ARTIFACTS_DIR)"
	cp backend/__init__.py "$(ARTIFACTS_DIR)/backend/"
	cp -R backend/agent backend/api backend/common backend/ingestion "$(ARTIFACTS_DIR)/backend/"
	find "$(ARTIFACTS_DIR)" -type d -name __pycache__ -prune -exec rm -rf {} +

build-ScoringTriggerFunction:
	mkdir -p "$(ARTIFACTS_DIR)/backend" "$(ARTIFACTS_DIR)/config"
	cp backend/__init__.py "$(ARTIFACTS_DIR)/backend/"
	cp -R backend/agent backend/api backend/common backend/scoring "$(ARTIFACTS_DIR)/backend/"
	cp config/scoring.v1.json "$(ARTIFACTS_DIR)/config/"
	find "$(ARTIFACTS_DIR)" -type d -name __pycache__ -prune -exec rm -rf {} +
