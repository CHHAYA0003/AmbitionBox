from flask import Flask, render_template, request
import pandas as pd
import os
import webbrowser
import matplotlib.pyplot as plt
import re

app = Flask(__name__)

CSV_PATH = os.path.join("scraped_data", "all_processed_combined.csv")

df = pd.read_csv(CSV_PATH)

df.columns = df.columns.str.strip()

if "Location" not in df.columns and "other" in df.columns:
    df.rename(columns={"other": "Location"}, inplace=True)

if "Rating" not in df.columns and "rating" in df.columns:
    df.rename(columns={"rating": "Rating"}, inplace=True)

if "Industry" not in df.columns and "field" in df.columns:
    df.rename(columns={"field": "Industry"}, inplace=True)

if "Company" not in df.columns and "company_" in df.columns:
    df.rename(columns={"company_": "Company"}, inplace=True)

if "Location" in df.columns:
    df["Location"] = df["Location"].astype(str).str.split("+").str[0].str.strip()


if "Rating" in df.columns:
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")


@app.route("/")
def home():
    locations = sorted(df["Location"].dropna().unique().tolist()) if "Location" in df.columns else []
    industries = sorted(df["Industry"].dropna().unique().tolist()) if "Industry" in df.columns else []

    return render_template("home.html", locations=locations, industries=industries)


@app.route("/submit", methods=["POST"])
def submit():
    city = request.form.get("Location")
    industry = request.form.get("industry")
    rating = request.form.get("rating")
    output = request.form.get("output")

    filtered = df.copy()

    if city and city != "Select City":
        filtered = filtered[filtered["Location"].str.contains(city, case=False, na=False)]

    if industry and industry != "Select Industry":
        filtered = filtered[filtered["Industry"].str.contains(industry, case=False, na=False)]

    if rating and rating != "Select Rating":
        try:
            filtered = filtered[filtered["Rating"] >= float(rating)]
        except:
            pass

    display_city = "All Cities"
    if city and city != "Select City":
        display_city = city

    if output == "visual":


        if not os.path.exists("static"):
            os.makedirs("static")

        safe_city = "all"
        if city and city != "Select City":
            safe_city = city.lower().strip()
            safe_city = re.sub(r"[^a-z0-9_]+", "_", safe_city)

        chart1_name = f"top_companies_{safe_city}.png"
        chart2_name = f"top_industries_{safe_city}.png"

        chart1_path = os.path.join("static", chart1_name)
        chart2_path = os.path.join("static", chart2_name)

        if "Company" in filtered.columns:
            top_companies = filtered["Company"].dropna().value_counts().head(10)
        else:
            top_companies = filtered.iloc[:, 0].dropna().value_counts().head(10)

        plt.figure(figsize=(10, 5))
        top_companies.plot(kind="bar")
        plt.title(f"Top 10 Companies (Job Count) - {display_city}")
        plt.tight_layout()
        plt.savefig(chart1_path)
        plt.close()

        chart2 = None
        if "Industry" in filtered.columns:
            top_ind = filtered["Industry"].dropna().value_counts().head(10)

            plt.figure(figsize=(10, 5))
            top_ind.plot(kind="bar")
            plt.title(f"Top 10 Industries - {display_city}")
            plt.tight_layout()
            plt.savefig(chart2_path)
            plt.close()

            chart2 = chart2_name

        return render_template(
            "visualization.html",
            chart1=chart1_name,
            chart2=chart2
        )

    return render_template(
        "table.html",
        tables=filtered.to_html(classes="premium-table", index=False)
    )


if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000/")
    app.run(debug=True)
