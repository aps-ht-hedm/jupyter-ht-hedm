# Easy control for starting and stopping virtual beamline

# ----- Targets ----- #
.PHONY: vbstart vbstop list clean

vbstart:
	mkdir -p vbdata
	mkdir -p vbdata/data
	mkdir -p vbdata/db
	docker-compose up -d

vbstop:
	docker-compose down

clean:
	rm -rvf vbdata

list:
	@echo "OPTIONS AVAILABLE:"
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null \
	| awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' \
	| sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs
