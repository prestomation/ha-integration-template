# Installation

Install Example Integration through HACS, or copy it into your configuration by hand.

## Install with HACS

1. In HACS, open the menu and select **Custom repositories**.
2. Add the repository URL with the type **Integration**.
3. Find **Example Integration** in HACS and select **Download**.
4. Restart Home Assistant.

## Install by hand

1. Download `example_integration.zip` from the latest GitHub release.
2. Unzip it into `config/custom_components/example_integration/`.
3. Restart Home Assistant.

## Add the integration

1. Go to **Settings** > **Devices & services**.
2. Select **Add integration** and find **Example Integration**.
3. Confirm the dialog.

The integration accepts 1 config entry. After setup, the panel shows in the sidebar and
the card shows in the card picker of each dashboard.

## Beta versions

A beta version is a GitHub pre-release. To install one, open the integration in HACS,
turn on **Show beta versions**, then download the version.
