# Introduction:

With the ability to conduct safe peer-to-peer transactions
without the need for a central authority like a bank,
cryptocurrency has quickly become a contemporary type
of digital currency. Because of its decentralized structure,
transparency, and trading and investment potential, it has
become increasingly popular throughout the world in
recent years. Cryptocurrency can now be bought, sold,
and used to buy goods and services on a number of online
platforms.

The goal of this project, "Crypto-Based Marketplace and
Trading System using Python and MySQL," is to show how
a computer-based system can automate digital purchases
and cryptocurrency trading. The system allows a user to
manage virtual cryptocurrency holdings, check real-time
cryptocurrency prices, and buy goods from a marketplace
with cryptocurrency rather than cash. In addition to
managing items in the marketplace, an administrator can
keep an eye on transaction records.

The main programming language used in the project is
Python, and the database system used to store user
balances, cryptocurrency holdings, transaction histories,
and marketplace goods is MySQL. An external API is used
to retrieve current cryptocurrency prices from the
internet. This combination of database connectivity and
programming logic allows the system to replicate a
simplified working model of real-world
cryptocurrency usage.

Overall, this project shows how contemporary financial
technologies can be integrated with e-commerce
platforms and emphasizes the significance of secure data
management.


# Analysis:
The objective of the system is to simulate three primary
functionalities:

### 1. Crypto Trading
Users can purchase cryptocurrencies using their
available INR balance and sell them back based on realtime market prices.

### 2. Virtual Marketplace Purchases
Users can utilize their crypto holdings to buy listed
products. These purchases are also stored in the
backend database.

### 3. Administrative Control
An admin role (switched through password verification)
allows:
- Managing INR balance for the user
- Adding or removing products in the marketplace
- Viewing all transaction history (crypto +
marketplace)

This promotes understanding of:
- Transaction logs
- Financial operations
- Data persistence using SQL
- API usage for real-time pricing

The solution combines fundamental programming logic
with practical financial database operations,
demonstrating how software can support modern
economic models.


# Requirements:

### Hardware Requirements
- A personal computer or laptop
- Minimum 4 GB RAM (recommended 8 GB)
- At least 200 MB free storage
- Stable internet connection (for real-time price API
requests)

### Software Requirements
- Operating System: Windows / macOS / Linux
- Python 3.10 or above
- MySQL Server and MySQL Workbench
- Required Python Libraries:  
&emsp; mysql.connector  
&emsp; requests  
&emsp; tabulate (optional for better formatting)  


# Data Collection:
In order to replicate a realistic digital trading
environment, this project requires precise and organized
data management. Both internal user interactions with the
system and external real-time cryptocurrency market
price retrieval are used to gather the data. Five relational
tables are used in a MySQL database to store all pertinent
data. Consistency, data integrity, and trustworthy financial
tracking are guaranteed by these tables.

## A. External Live Market Data
Live cryptocurrency prices are obtained through an online
price API. This data is used immediately to calculate
transaction values.
Externally collected data includes:
- Cryptocurrency Name (e.g., Bitcoin, Ethereum)
- Current Price in INR
- Time of Last Market Price Update

This information is temporary and is not saved in the
database. It is fetched only when necessary, to maintain
pricing accuracy.

## B. Internal Data Collection and Database Storage
All monetary and marketplace interactions are
recorded permanently inside the database.
The five tables are described below:

### 1. crypto_holdings
Purpose: To keep track of the user’s accumulated
cryptocurrency for each supported coin.  
This table allows the system to retrieve and update
holdings efficiently after each trade.

### 2. user_balance
Purpose: To store the amount of Indian Rupees (INR)
available to the user.  
This enables controlled modification of user funds —
especially by the admin. 

### 3. items
Purpose: To maintain the catalogue of products that can
be purchased using cryptocurrency.  
This table ensures that all marketplace items are properly
listed before purchases take place.

### 4. crypto_transactions
Purpose: To record all buy and sell operations involving
cryptocurrency.  
This creates a permanent audit log of trading activities. 

### 5. marketplace_purchases
Purpose: To log purchases of marketplace items using
cryptocurrency.  
This table ensures complete transparency of product
purchases and crypto expenditure.


# Summary
The data collection methodology in this project combines
real-time financial data from an online API with securely
stored transaction records in a MySQL database. Through
the use of five well-designed tables, the system ensures
that every action affecting finances and inventory is
recorded, validated, and traceable. This reflects how
actual financial technology platforms operate in
international digital markets.
