# Deployment and rollback preparation

The source repository is [pseudorational/financial-dashboard](https://github.com/pseudorational/financial-dashboard), with private visibility. The Streamlit app has not yet been deployed. No hosting account or data subscription was created during implementation.

## Streamlit Community Cloud settings

- Repository: `pseudorational/financial-dashboard`
- Branch: `main`
- Main file path: `app.py`
- Advanced settings → Python version: `3.12`
- Secrets: leave blank for the default synthetic demo
- After deployment, Settings → Sharing → public enables a publicly accessible app while keeping the source repository private.

1. Run the pinned Python 3.12 environment, `python -m pytest -q`, and the browser acceptance journeys described in verification.md. Review synthetic notices, all four tabs, two-symbol isolation, missing-data states, layout, and Plotly controls.
2. Create the chosen GitHub repository with these project files, `requirements.txt`, `.streamlit/config.toml`, and `app.py`. Preserve the original specification with the release source. Keep `.venv`, secrets, logs, caches, browser authentication state, and raw restricted data excluded. The provided GitHub Actions workflow installs the pinned development environment and runs offline tests.
3. For Streamlit Community Cloud, select that repository, the tested release commit/branch, `app.py`, and Python 3.12. Keep `DASHBOARD_MODE=demo` (or omit it). No secrets are needed. If this project remains nested in a larger repository, use its repository-relative app path and confirm the host locates its requirements/config; a dedicated project-root repository avoids that ambiguity.
4. Verify the actual hosted build and health, cold start, layout at desktop/mobile sizes, two-company switching, degraded regions, service logs, and session isolation. Do not claim host performance, free-tier availability, or uptime without measurement and a fresh review of current hosting terms and resource limits.
5. Record deployed commit, environment configuration, dependencies, verification results, and a last-known-good commit. Treat local cache contents as disposable.

For rollback, restore the last-known-good commit on the selected deployment branch and redeploy/reboot using the host's controls. Verify the displayed company, mode notice, charts, dates, and four tabs. If data rights or a provider fail, disable affected live mode and redeploy an explicitly labeled demo or an unavailable state. Never substitute synthetic values under a real company's label.

For local use, stop with Ctrl+C and restart with `streamlit run app.py`. The preview binds only to 127.0.0.1. Changing code requires a restart because file watching is disabled in the checked-in configuration.

Official references to recheck when deploying: [Community Cloud deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud), [app management](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app), and [secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).
