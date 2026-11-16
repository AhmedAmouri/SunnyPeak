# SunnyPeak Solutions

Estimate the DC energy from a fixed solar array at your site using historical weather.

The [user guide](docs-source/index.md) explains weather setup, simulation, optimization, CSV export, and plotting through one worked example. It includes a [core reference](docs-source/index.md#core-reference).

## Run a simulation

Clone the repository or extract the ZIP. Install the dependencies from the project folder with Python 3.10 or later.

```bash
python -m pip install -r requirements.txt
```

In Python, import the simulation function and supply your site, weather year, and panel layout. This example uses the bundled weather and catalog panel.

```python
from sunnypeak import simulate_solar

result = simulate_solar(
    latitude=34.73,
    longitude=10.76,
    year=2020,
    panel_name="PV-MJT250GB",
    panel_count=12,
    tilt_deg=20,
    azimuth_deg=135,
)
print(f"{result['annual_kwh']:,.0f} kWh")
```

For weather outside the bundle, see [Get weather data](docs-source/index.md#get-weather-data).

## Put the project on GitHub

Create an empty repository on GitHub, then run these commands from the folder containing this README. Replace `YOUR-USERNAME` and `YOUR-REPOSITORY` with the values from your repository URL.

```bash
git init -b main
git add .
git commit -m "Add SunnyPeak Solutions"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

GitHub renders the Markdown pages directly in the repository. See the [GitHub instructions for importing local code](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

## Generate the HTML guide with Sphinx

Install the documentation dependencies, then run Sphinx from the repository root.

```bash
python -m pip install -r requirements-docs.txt
python -m sphinx -b html -d .sphinx-doctrees docs-source docs
```

Sphinx renders `docs-source/index.md` and creates the `docs/` folder. Open `docs/index.html` in a browser after the build.

### Host the guide on GitHub Pages

Build the HTML first. Then commit and push the generated `docs/` folder, including the `.nojekyll` file created by Sphinx. In your repository, go to **Settings → Pages**, choose **Deploy from a branch**, select **main** and **/docs**, and save. After deployment, the Pages settings show the site URL. See the [GitHub Pages setup instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
