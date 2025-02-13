import requests
import pandas as pd
import json


class RequestEngine:
    def __init__(self, authToken):
        self.authToken = authToken
        self.marketInfo = None
        self.dailyStocksX = []
        self.dailyStocksY = []
        self.stockRegions = []
        self.companyInfo = []
        # SAMO API NIE WYRZUCA INFORMACJI O TYCH MARKETACH TAKZE NIE WIEM W OGOLE PO CO TO JEST ZAWARTE. DLATEGO TO ZOSTALO WYLACZONE
        self.marketExclusions = ["Frankfurt", "India/Bombay", "Brazil/Sao Paolo", "Germany", "Hong Kong", "India", "Portugal",
                                  "Spain", "France", "Japan", "Canada", "United Kingdom", "Mainland China", "XETRA",
                                 "Brazil", "Mexico", "South Africa"] #wyłączenie z filtru po lewej. Jak klikamy wyszukaj to generuje nam tylko akcje z regionów, których nie ma tutaj
        
        self.countryExclusions = ["Germany", "Hong Kong", "India", "Portugal", "Spain", "France", "Japan", "Canada", "United Kingdom", "Mainland China", "Brazil", "Mexico", "South Africa"] #wyłączenie z filtru z krajami (po prawej)
        #companyInfo

    def removeEmptySpaces(self):
        # Read the CSV file into a DataFrame
        file_path = "MarketNames.csv"  # Replace with your actual file path
        df = pd.read_csv(file_path)

        # Remove empty spaces from all string values in the DataFrame
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # Save the cleaned DataFrame back to a CSV file
        output_file = "MarketNames.csv"
        df.to_csv(output_file, index=False)

    def loadFromJson(self, fileNameWithoutExtension):

        with open(f"{fileNameWithoutExtension}.json", "r") as f:
            content = f.read()
        content = json.loads(content)

        return content

    def returnIndexFromMarketInfoList(self, region):
        for id, market in enumerate(self.marketInfo):
            if market["market_type"] == "Equity":

                if region in f"{market['region']} {market['primary_exchanges']}":
                    return id

    def loadMarketInfo(self):
        with open("marketStatus.json", "r") as f:
            content = f.read()
        content = json.loads(content)
        self.marketInfo = content["markets"]
    
    def loadMarketRegions(self):
        for market in self.marketInfo:
            print(market)
            if market["market_type"] == "Equity":
                if market["region"] not in self.countryExclusions:
                    self.stockRegions.append(f"{market['region']}; {market['primary_exchanges']}")

    def getMarketOpenHours(self, marketRegion):

        for market in self.marketInfo:
            if market["market_type"] == "Equity":

                if marketRegion in f"{market['region']} {market['primary_exchanges']}":
                    return market["local_open"], market["local_close"]
            
    def getRegionNotes(self, marketRegion):
        for market in self.marketInfo:
            if market["market_type"] == "Equity":
                if marketRegion in f"{market['region']} {market['primary_exchanges']}":
                    return market["notes"]        

    def isMarketOpen(self, marketRegion):
        for market in self.marketInfo:
            if market["market_type"] == "Equity" and (market["region"] == marketRegion or market["primary_exchanges"] == marketRegion) and market["current_status"] == "open":
                return True
    #Market Status
    def marketStatusRequest(self):
        response = requests.get(f"https://www.alphavantage.co/query?function=MARKET_STATUS&apikey={self.authToken}")
        self.saveToJson(response, "marketStatus")
    
    def saveToJson(self, response, nameOfFile):
        jsonContent = response.content.decode('utf-8')

        #saves market status as temporary file
        jsonContent = json.loads(jsonContent)
        with open(f"{nameOfFile}.json", "w") as f:
            f.write(json.dumps(jsonContent))

    
    def findCompany(self, keywords, region):
        # response = requests.get(f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={keywords}{region}&apikey={self.authToken}")
        response = requests.get(f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={keywords}&apikey={self.authToken}")
        # response = requests.get("https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords=tesco&apikey=demo")
        self.saveToJson(response, "foundCompanies")

    def loadFoundCompanies(self):
        with open(f"foundCompanies.json", "r") as f:
            content = f.read()
        content = json.loads(content)
        self.foundCompanies = content

    def getFoundCompaniesNamesFromJson(self, chosenRegion, isCountryFilter):
        listOfCompaniesNames = []

        for match in self.foundCompanies["bestMatches"]:

            if isCountryFilter:
                if match["3. type"] == "Equity" and match["4. region"] in chosenRegion:
                    listOfCompaniesNames.append(f"{match['1. symbol']}; {match['2. name']}; {match['4. region']}")
            else:
                # for exclusion in self.marketExclusions:
                #     print(exclusion)
                if match["3. type"] == "Equity":
                    if match["4. region"] not in self.marketExclusions:
                        listOfCompaniesNames.append(f"{match['1. symbol']}; {match['2. name']}; {match['4. region']}")
        
        if not listOfCompaniesNames:
            listOfCompaniesNames.append("Nie znaleziono podanych akcji")
        return listOfCompaniesNames
    
    def findCompanyInfo(self, stockSymbol):
        #self.combo_name
        response = requests.get(f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={stockSymbol}&apikey={self.authToken}")
        

        self.saveToJson(response, "companyInfo")

        self.companyInfo = self.loadFromJson("companyInfo")
    
    def getDailyStocks(self, stockSymbol):
        """per 5 minutes"""
        # url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&outputsize=full&apikey=demo" # testowy url
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stockSymbol}&interval=5min&outputsize=full&apikey={self.authToken}" #docelowy url
        response = requests.get(url)

        self.saveToJson(response, "dailyStocks")

        dailyStocks = self.loadFromJson("dailyStocks")
        self.dailyStocksX.clear()
        self.dailyStocksY.clear()
        numOfIterations = 1
        for period in dailyStocks["Time Series (5min)"]:    
            # print(period)
            self.dailyStocksX.append(period)

            # print(dailyStocks["Time Series (5min)"][period]["2. high"])
            self.dailyStocksY.append(float(dailyStocks["Time Series (5min)"][period]["2. high"]))
            # tyle iteracji bo tyle ma 16 h w podziale na 5 min
            numOfIterations += 1
            if numOfIterations >= 192:
                break

        self.dailyStocksX.reverse()
        self.dailyStocksY.reverse()
    
    def getMonthlyStocks(self, stockSymbol):
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={stockSymbol}&apikey={self.authToken}" #docelowy url
        # url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo" #testowy url
        response = requests.get(url)

        self.saveToJson(response, "dailyStocks")

        dailyStocks = self.loadFromJson("dailyStocks")
        self.dailyStocksX.clear()
        self.dailyStocksY.clear()
        numOfIterations = 0
        for day in dailyStocks["Time Series (Daily)"]:    
            # print(day)
            self.dailyStocksX.append(day)

            # print(dailyStocks["Time Series (Daily)"][day]["2. high"])
            self.dailyStocksY.append(float(dailyStocks["Time Series (Daily)"][day]["2. high"]))
            numOfIterations += 1
            if numOfIterations >= 30:
                break

        self.dailyStocksX.reverse()
        self.dailyStocksY.reverse()

    
    def getWeeklyStocks(self, stockSymbol):
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={stockSymbol}&apikey={self.authToken}" #docelowy url
        # url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo" # testowy url
        response = requests.get(url)

        self.saveToJson(response, "dailyStocks")

        dailyStocks = self.loadFromJson("dailyStocks")
        self.dailyStocksX.clear()
        self.dailyStocksY.clear()
        numOfIterations = 0
        for day in dailyStocks["Time Series (Daily)"]:    
            # print(day)
            self.dailyStocksX.append(day)

            # print(dailyStocks["Time Series (Daily)"][day]["2. high"])
            self.dailyStocksY.append(float(dailyStocks["Time Series (Daily)"][day]["2. high"]))
            numOfIterations += 1
            if numOfIterations >= 7:
                break

        self.dailyStocksX.reverse()
        self.dailyStocksY.reverse()

