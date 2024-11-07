# Import necessary libraries
from pytrends.request import TrendReq
import streamlit as st
import requests
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import os
from groq import Groq

# Set up the Groq LLaMA client with your API key
client = Groq(api_key="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")

# Country and states dictionary with Google Trends-compatible geo codes
country_states = {
    "United States": {"code": "US", "states": {"California": "US-CA", "Texas": "US-TX", "New York": "US-NY", "Florida": "US-FL", "Illinois": "US-IL"}},
    "India": {"code": "IN", "states": {"Maharashtra": "IN-MH", "Karnataka": "IN-KA", "Delhi": "IN-DL", "Tamil Nadu": "IN-TN", "Uttar Pradesh": "IN-UP"}},
    "Australia": {"code": "AU", "states": {"New South Wales": "AU-NSW", "Victoria": "AU-VIC", "Queensland": "AU-QLD", "Western Australia": "AU-WA", "South Australia": "AU-SA"}},
    "United Arab Emirates": {"code": "AE", "states": {"Abu Dhabi": "AE-AZ", "Dubai": "AE-DU", "Sharjah": "AE-SH"}},
    "Saudi Arabia": {"code": "SA", "states": {"Riyadh": "SA-01", "Makkah": "SA-02", "Madinah": "SA-03", "Eastern Province": "SA-04"}}
}

# Function to get Google Trends data with a fixed timeframe
def get_google_trends(keyword, geo_code):
    pytrends = TrendReq(hl='en-US', tz=360)
    timeframe = 'today 30-d'  # Fixed timeframe
    pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo_code, gprop='')
    data = pytrends.interest_over_time()
    return data

# Function to scrape Amazon Best Sellers (for example, in Electronics)
def get_amazon_best_sellers():
    url = "https://www.amazon.com/Best-Sellers/zgbs"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find best-selling products on the page
    products = []
    for item in soup.select(".zg-item-immersion"):
        title = item.select_one(".p13n-sc-truncated").get_text(strip=True)
        rating = item.select_one(".a-icon-alt").get_text(strip=True) if item.select_one(".a-icon-alt") else "No rating"
        price = item.select_one(".p13n-sc-price").get_text(strip=True) if item.select_one(".p13n-sc-price") else "No price"
        products.append({"title": title, "rating": rating, "price": price})
    
    return products[:5]  # Return the top 5 products

# Function to query the Groq LLaMA model
def get_llama_response(query):
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": query}],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"LLaMA API Error: {e}"

# Streamlit Interface
def main():
    st.title('Winning Product Finder Bot with Trend Analysis')

    # Dropdown to select country
    country = st.selectbox("Select a country", list(country_states.keys()))
    country_data = country_states[country]
    country_code = country_data["code"]

    # Optional state selection
    state = st.selectbox("Select a state/province (optional)", ["All"] + list(country_data["states"].keys()))
    state_code = country_data["states"].get(state, None) if state != "All" else country_code

    # Input for product keyword
    keyword = st.text_input("Enter a product keyword (e.g., 'wireless earbuds')")

    # Button to fetch trends and suggest products
    if st.button("Find Winning Product"):
        if keyword:
            # Use country or state code for geo
            geo_code = state_code if state_code else country_code

            try:
                # Get Google Trends data
                trend_data = get_google_trends(keyword, geo_code)
                if not trend_data.empty:
                    # Calculate trend percentage
                    trend_data['Percentage'] = (trend_data[keyword] / trend_data[keyword].max()) * 100
                    avg_percentage = trend_data['Percentage'].mean()

                    # Display trend data
                    st.write(f"Trend data for '{keyword}' in {country} ({'state' if state != 'All' else 'country'} level):")
                    st.line_chart(trend_data['Percentage'])
                    st.write(trend_data[['Percentage']])

                    # Display trend popularity
                    st.write(f"Current popularity of '{keyword}': **{avg_percentage:.2f}%**")
                else:
                    st.write("No trend data found for the selected region and keyword.")
            except Exception as e:
                st.write(f"Error fetching Google Trends data: {e}")

            # Get top Amazon best-sellers
            st.write("Top Amazon Best Sellers:")
            amazon_products = get_amazon_best_sellers()
            for product in amazon_products:
                st.write(f"Product: {product['title']} | Rating: {product['rating']} | Price: {product['price']}")

            # Explanation feature
            st.write("If you have any questions about this trend, enter your question below:")
            query = st.text_input("Ask about the trend")
            if query:
                llama_response = get_llama_response(query)
                st.write("LLaMA Model Response:")
                st.write(llama_response)
        else:
            st.write("Please enter a product keyword.")

if __name__ == "__main__":
    main()
