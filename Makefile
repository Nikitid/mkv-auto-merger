SHELL := /usr/bin/env bash

.DEFAULT_GOAL := help

.PHONY: help setup lint format test

help:
	@printf '%s\n' 'Available commands:'
	@printf '  %-12s %s\n' 'setup' 'Install or verify local development dependencies.'
	@printf '  %-12s %s\n' 'lint' 'Run all lint checks.'
	@printf '  %-12s %s\n' 'format' 'Format shell scripts.'
	@printf '  %-12s %s\n' 'test' 'Run tests.'

setup:
	./scripts/setup.sh

lint:
	./scripts/lint.sh

format:
	shfmt -w -i 2 scripts tests

test:
	./scripts/test.sh
