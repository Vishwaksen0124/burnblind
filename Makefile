.PHONY: build-EventApiFunction

build-EventApiFunction:
	mkdir -p "$(ARTIFACTS_DIR)/backend"
	cp backend/__init__.py "$(ARTIFACTS_DIR)/backend/"
	cp -R backend/api backend/common "$(ARTIFACTS_DIR)/backend/"
	find "$(ARTIFACTS_DIR)" -type d -name __pycache__ -prune -exec rm -rf {} +
