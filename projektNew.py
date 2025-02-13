import tkinter as tk
from tkinter import simpledialog, messagebox

from tkinter import ttk
import platform
import ctypes
import subprocess
import re
from RequestsEngine import RequestEngine

import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class UserInterface:
    def __init__(self):
        self.userOS = None

        screenResolution = self.getScreenGeometry()
        appSize = int(screenResolution[0] * 0.45), int(screenResolution[1] * 0.65)

        self.afterID = None
        self.chartPeriod = None
        self.chosenStock = None
        

        self.chosenMarket = "Wybierz kraj"

        self.connectRequestEngine()

        self.createAppWindow(appSize)

    def createAppWindow(self, appSize):
        self.root = tk.Tk()
        self.root.title("Aplikacja do monitorowania akcji")

        self.root.geometry(f"{appSize[0]}x{appSize[1]}")
        # self.root.minsize(appSize[0], appSize[1])

        #JESLI 4k TO SCALING 3.0. JESLI FULLHD 1.0. DO SPRAWDZENIA
        if self.userOS == "Windows":
            scaling_factor = self.root.winfo_fpixels('1i') / 65.0
            print("SCALING FACTOR: ", scaling_factor)
            self.root.tk.call('tk', 'scaling', scaling_factor)
        elif self.userOS == "Darwin":
            scaling_factor = self.root.winfo_fpixels('1i') / 50.0
            self.root.tk.call('tk', 'scaling', scaling_factor)
        else:
            scaling_factor = self.root.winfo_fpixels('1i') / 50.0
            print("SCALING FACTOR: ", scaling_factor)
            self.root.tk.call('tk', 'scaling', scaling_factor)
        # self.root.maxsize(appSize[0], appSize[1])

        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=3)
        self.root.grid_rowconfigure(3, weight=0)
        # self.root.grid_rowconfigure(4, weight=1)

        self.root.grid_columnconfigure(0, weight=1)
        # self.root.grid_columnconfigure(1, weight=1)


        #initializes stock chooser frame and widgets inside
        self.initializeStockChooserFrame()
        #initializes market info frame and widgets inside
        self.initializeMarketInfoFrame()
        #initializes stock info frame and widgets inside
        self.initializeChartAndStockFrame()
        #initializes company info frame and widgets inside
        self.initializeCompanyInfoAndAnalystRecommendationsFrame()
        # self.initializeCompanyInfoFrame()

        # self.initializeAnalystRecommendationsFrame()
        self.root.protocol("WM_DELETE_WINDOW", self._onClose)
        try:
            self.root.mainloop()
        except KeyError:
            self.outOfRequestsError()

    def _onClose(self):
        plt.close(self.fig)  # Close the Matplotlib figure
        self.root.destroy()  # Destroy the Tkinter window

    def authorizeUser(self):
        return simpledialog.askstring("Klucz API", "Proszę o podanie klucza API:")
    
    def outOfRequestsError(self):
        messagebox.showerror("Błąd", "Ilość darmowych requestów w API została wykorzystana. Program nie będzie pobierać danych. Spróbuj ponownie później.")

    def connectRequestEngine(self):
        apiKey = self.authorizeUser()

        if apiKey is None:
            exit()

        self.requestEngine = RequestEngine(apiKey)

        ######################################################
        # W TYM API JEST LIMIT DZIENNY, KTÓRY MA TYLKO 25 REQUESTÓW. JEŚLI PRZEKROCZY SIĘ TEN LIMIT TO TRZEBA WYŁĄCZYĆ TĄ FUNKCJĘ.
        try:
            self.requestEngine.marketStatusRequest()
            self.requestEngine.loadMarketInfo()
            self.requestEngine.loadMarketRegions()
        except KeyError:
            self.outOfRequestsError()

        ######################################################

    def getScreenGeometry(self):
        self.userOS = platform.system()

        if self.userOS == "Windows":
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        elif self.userOS == "Darwin":
            results = str(
            subprocess.Popen(['system_profiler SPDisplaysDataType'], stdout=subprocess.PIPE, shell=True).communicate()[0])
            res = re.search(r'Resolution: \d* x \d*', results).group(0).split(' ')
            width, height = res[1], res[3]
            screensize = int(width), int(height)
        # else:
        #     screensize = 1980, 1080
        return screensize
    
    def initializeStockChooserFrame(self):
        stockChooserFrame = tk.Frame(self.root)
        self.initializeStockChooserWidgets(stockChooserFrame)

        stockChooserFrame.grid(row=0, column=0, sticky='nsew')

        stockChooserFrame.grid_columnconfigure(0, weight=2)
        stockChooserFrame.grid_columnconfigure(1, weight=2)
        stockChooserFrame.grid_columnconfigure(2, weight=1)
        stockChooserFrame.grid_columnconfigure(3, weight=2)
        #row 1

    def initializeStockChooserWidgets(self, stockChooserFrame):
        def initializeBinds():
            combo_country.bind("<<ComboboxSelected>>", lambda event: self.onComboxCountrySelect(event, combo_country, combo_country.get().split(";")[0]))
            #binds enter key and passes event var and name of a country from combox
            self.combo_name.bind('<Return>', lambda event: self.onComboxStockEnter(event, combo_country.get()))
            self.combo_name.bind("<<ComboboxSelected>>", lambda event: self.onComboxStockSelect(event, combo_country))

            enableLabelCountryCheckbox.bind("<Button-1>", lambda event: self.onCheckBoxClick(event, combo_country))


        label_name = tk.Label(stockChooserFrame, text="Nazwa firmy (akcja):")
        label_name.grid(row=0, column=0, sticky='ew')

        #TODO COMBOBOX AUTOFILL OPTION
        self.comboVar = tk.StringVar()
        self.combo_name = ttk.Combobox(stockChooserFrame, textvariable=self.comboVar)
        self.combo_name.grid(row=0, column=1, sticky='ew')
        self.combo_name.set("Wybierz akcję")

        # self.comboVar.trace_add("write", self.onComboxStockSelect)
        self.checkboxBool = tk.BooleanVar()
        enableLabelCountryCheckbox = tk.Checkbutton(stockChooserFrame, variable=self.checkboxBool)
        enableLabelCountryCheckbox.grid(row=0, column=2, sticky="e")

        label_country = tk.Label(stockChooserFrame, text="Kraj akcji:")
        label_country.grid(row=0, column=3, sticky='ew')

        #TODO TRZEBA DO ZROBIĆ ZE STRINGVAR A NIE TAK JAK TERAZ
        combo_country = ttk.Combobox(stockChooserFrame, values=self.requestEngine.stockRegions, state="disabled")
        combo_country.grid(row=0, column=3, sticky='ew')
        combo_country.set(self.chosenMarket)

        initializeBinds()

    def onCheckBoxClick(self, event, comboxCountry):

        if not self.checkboxBool.get():
            comboxCountry["state"] = "readonly"
        else:
            comboxCountry["state"] = "disabled"

    def onComboxCountrySelect(self, event, combox, chosenRegion):
        try:
            openHours = self.requestEngine.getMarketOpenHours(chosenRegion)
            self.updateMarketInfoOpenHours(openHours)
            self.updateMarketStatus(chosenRegion)
            self.updateAdditionalNotes(chosenRegion)
        except KeyError:
            self.outOfRequestsError()


    def onComboxStockEnter(self, event, chosenRegion):
        try:
            self.requestEngine.findCompany(self.comboVar.get(), chosenRegion)
            self.requestEngine.loadFoundCompanies()
            print(self.comboVar.get())
            # print(chosenRegion) #TUTAJ CHOSEN REGION WYWALA GLUPOTE
            foundCompanies = self.requestEngine.getFoundCompaniesNamesFromJson(chosenRegion, self.checkboxBool.get())
            self.combo_name.config(values=foundCompanies)
            self.combo_name.event_generate('<Down>')
        except KeyError:
            self.outOfRequestsError()

    def onComboxStockSelect(self, event, comboCountry):


        region = self.combo_name.get().split(";")[2].strip()
        self.requestEngine.findCompanyInfo(self.combo_name.get().split(";")[0].strip())


        self.onComboxCountrySelect("", comboCountry, region)
        comboCountry.current(self.requestEngine.returnIndexFromMarketInfoList(region))

        self.updateCompanyInfo()
        self.updateAnalystRating()

        self.rememberChosenStock()

        self.setToMonthly() #2 funkcje aktywują odświeżanie wykresu przy wyborze firmy
        self.startPeriodicTask()

    def rememberChosenStock(self):
        self.chosenStock = self.combo_name.get().split(";")[0].strip()
        print(self.chosenStock)

    def updateCompanyInfo(self):
        #"Name": "Intel Corporation",
        try:
            name = self.requestEngine.companyInfo["Name"]
            symbol = self.requestEngine.companyInfo["Symbol"]
            sector = self.requestEngine.companyInfo["Sector"]
            country = self.requestEngine.companyInfo["Country"]
            address = self.requestEngine.companyInfo["Address"]
            fiscalYear = self.requestEngine.companyInfo["FiscalYearEnd"]
        except Exception as e:
            messagebox.showerror(message=f"Coś poszło nie tak przy pobieraniu informacji o firmie! Pole informacje o firmie nie będą uzupełnione. Error code: {type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")


        self.companyName.configure(text=f"Nazwa: {name}")
        #  "Symbol": "INTC",
        self.companySymbol.configure(text=f"Symbol: {symbol}")
        #    "Sector": "MANUFACTURING",
        self.sectorName.configure(text=f"Sektor: {sector}")
        #    "Country": "USA",
        self.countryName.configure(text=f"Kraj firmy: {country}")
        #    "Address": "2200 MISSION COLLEGE BLVD, RNB-4-151, SANTA CLARA, CA, US",
        self.addressName.configure(text=f"Adres: {address}")
        #    "FiscalYearEnd": "December",
        self.fiscalYearEnd.configure(text=f"Koniec roku fiskalnego: {fiscalYear}")

    def updateAnalystRating(self):


        try:
            targetPrice = self.requestEngine.companyInfo["AnalystTargetPrice"]
            strongBuy = self.requestEngine.companyInfo["AnalystRatingStrongBuy"]
            buy = self.requestEngine.companyInfo["AnalystRatingBuy"]
            hold = self.requestEngine.companyInfo["AnalystRatingHold"]
            sell = self.requestEngine.companyInfo["AnalystRatingSell"]
        except Exception as e:
            messagebox.showerror(message=f"Coś poszło nie tak przy pobieraniu danych o giełdzie. Informacje o rekomendacjach analityków nie zostaną wyświetlone. Error code: {type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")

        self.targetPrice.configure(text=f"Cena docelowa: {targetPrice}")
        self.ratingStrongBuy.configure(text=f"Zdecydowanie kupuj: {strongBuy}")
        self.ratingBuy.configure(text=f"Kupuj: {buy}")
        self.ratingHold.configure(text=f"Trzymaj: {hold}")
        self.ratingSell.configure(text=f"Sprzedaj: {sell}")
        
    def updateMarketInfoOpenHours(self, openHours):

        self.openingHours.config(text=f"Godzina otwarcia: {openHours[0]}")
        self.closingHours.config(text=f"Godzina zamknięcia: {openHours[1]}")

    def updateMarketStatus(self, marketRegion):
        isMarketOpen = self.requestEngine.isMarketOpen(marketRegion)
        if isMarketOpen:
            self.marketStatus.config(text="Status giełdy: Otwarta")
        else:
            self.marketStatus.config(text="Status giełdy: Zamknięta")

    def updateAdditionalNotes(self, marketRegion):
        self.additionalNotes.config(state="normal")
        self.additionalNotes.delete(0, tk.END)
        # Insert new text
        regionNotes = self.requestEngine.getRegionNotes(marketRegion)

        
        self.additionalNotes.insert(0, regionNotes)
        self.additionalNotes.config(state="readonly")
        # self.root.update_idletasks()
        # self.root.update()

    def initializeMarketInfoFrame(self):
        marketInfoFrame = tk.LabelFrame(self.root, text="Informacje o giełdzie")
        self.initializeMarketInfoWidgets(marketInfoFrame)
        marketInfoFrame.grid_columnconfigure(0, weight=2)
        marketInfoFrame.grid_columnconfigure(1, weight=2)
        marketInfoFrame.grid_rowconfigure(2, weight=1)
        
        marketInfoFrame.grid(row=1, sticky='nsew')
    
    def initializeMarketInfoWidgets(self, marketInfoFrame):
        #TODO DO DODATNIA LABELSY Z INFO O WYBRANYM MARKECIE
        padxValue = 2
        padyValue = 2

        self.openingHours = tk.Label(marketInfoFrame, text="Godzina otwarcia: ")
        self.openingHours.grid(row=0, column=0, padx=padxValue, pady=padyValue, sticky='nsw')

        self.closingHours = tk.Label(marketInfoFrame, text="Godzina zamknięcia: ")
        self.closingHours.grid(row=0,column=1, padx=padxValue, pady=padyValue, sticky='nsw')

        self.marketStatus = tk.Label(marketInfoFrame, text="Status giełdy: ")
        self.marketStatus.grid(row=1, column=0, padx=padxValue, pady=padyValue, sticky='nsw')

        additionalNotesFrame = tk.LabelFrame(marketInfoFrame, text="Dodatkowe informacje:", relief="flat")
        additionalNotesFrame.grid(row=2, column=0, columnspan=3, padx=padxValue, pady=padyValue, sticky='nsew')
        additionalNotesFrame.grid_columnconfigure(0, weight=1)
        additionalNotesFrame.grid_rowconfigure(0, weight=1)

        self.additionalNotes = tk.Entry(additionalNotesFrame, state="readonly")
        self.additionalNotes.grid(sticky='nsew')

    def initializeChartAndStockFrame(self):
        stockAndChartFrame = tk.Frame(self.root)
        self.initializeChartFrame(stockAndChartFrame)
        self.initializeStockInfoFrame(stockAndChartFrame)
        stockAndChartFrame.grid(row=2, sticky='nsew')

        stockAndChartFrame.grid_columnconfigure(0, weight=1)
        stockAndChartFrame.grid_columnconfigure(1, weight=5)
        stockAndChartFrame.grid_rowconfigure(0, weight=1)

    def initializeChartFrame(self, stockAndChartFrame):
        chartFrame = tk.Frame(stockAndChartFrame)
        
        chartFrame.grid_columnconfigure(0, weight=1)
        chartFrame.grid_columnconfigure(1, weight=1)
        chartFrame.grid_columnconfigure(2, weight=1)
        chartFrame.grid_columnconfigure(3, weight=1)
        chartFrame.grid_rowconfigure(1, weight=1)
        chartFrame.grid(row=0, column=1, sticky='nsew')

        self.initializeChartFrameWidgets(chartFrame)

    def initializeChartFrameWidgets(self, chartFrame):

        self.generateChartTools(chartFrame)

        dailyButton = tk.Button(chartFrame, text="Obecny dzień", command=lambda: [self.setToDaily(), self.updateChartData(self.chartPeriod), self.startPeriodicTask()]) 
        dailyButton.grid(column=0, row=3, sticky='nsew')
        weeklyButton = tk.Button(chartFrame, text="7 dni", command=lambda: [self.setToWeekly(), self.updateChartData(self.chartPeriod), self.startPeriodicTask()])
        weeklyButton.grid(column=1, row=3, sticky='nsew')
        monthlyButton = tk.Button(chartFrame, text="30 dni", command=lambda: [self.setToMonthly(), self.updateChartData(self.chartPeriod), self.startPeriodicTask()])
        monthlyButton.grid(column=2, row=3, sticky='nsew')
        stopRefresh = tk.Button(chartFrame, text="Zatrzymaj odświeżanie", command=lambda: self.stopPeriodicTask())
        stopRefresh.grid(column=3, row=3, sticky='nsew')

    def runPeriodically(self):
        # print("Wykonano daily")
        self.updateChartData(self.chartPeriod)
        self.afterID = self.root.after(300000, self.runPeriodically)  # Schedule it again

    def startPeriodicTask(self):
        if self.afterID is None:  # Prevent multiple calls
            self.runPeriodically()

    def stopPeriodicTask(self):
        if self.afterID:
            print(self.afterID)
            self.root.after_cancel(self.afterID)  # Cancel the scheduled task
            self.afterID = None  # Reset event ID

    def setToDaily(self):
        self.chartPeriod = "daily"

    def setToWeekly(self):
        self.chartPeriod = "weekly"

    def setToMonthly(self):
        self.chartPeriod = "monthly"

    def generateChartTools(self, chartFrame):
        if self.userOS == "Windows":
            self.fig, self.ax = plt.subplots(figsize=(1, 1), dpi=60)
        elif self.userOS == "Darwin":
            self.fig, self.ax = plt.subplots(figsize=(1, 1), dpi=50)
        else:
            self.fig, self.ax = plt.subplots(figsize=(1, 1), dpi=50)

        self.ax.plot(self.requestEngine.dailyStocksX, self.requestEngine.dailyStocksY, marker="o", linestyle="-", color="b")
        self.ax.tick_params(axis="both")

        self.canvas = FigureCanvasTkAgg(self.fig, master=chartFrame)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.grid(row=1, column=0, columnspan=4, sticky='nsew')

        # Add Navigation Toolbar for zoom & pan functionality
        toolbarFrame = tk.Frame(chartFrame)
        toolbarFrame.grid(row=2, column=0, columnspan=4, sticky='nsew')
        toolbar = NavigationToolbar2Tk(self.canvas, toolbarFrame)
        toolbar.update()
        toolbar.pack()

    def updateChartData(self, period):
        """ tego używamy do odpalenia całej funkcji generowania chartów"""
        def updateChart(period):

            self.ax.clear()


            self.ax.set_title(f"{self.chosenStock} Chart")
            self.ax.set_xlabel("") 
            self.ax.set_ylabel("Cena - najwyższa")

            self.ax.tick_params(axis="x", rotation=60)


            if period == "daily":
                self.ax.plot(self.requestEngine.dailyStocksX, self.requestEngine.dailyStocksY, marker=None, linestyle="-", color="g")
                self.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=12))  # Maximum 5 major ticks
            elif period == "weekly":
                self.ax.plot(self.requestEngine.dailyStocksX, self.requestEngine.dailyStocksY, marker=None, linestyle="-", color="b")
                self.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
            elif period == "monthly":
                self.ax.plot(self.requestEngine.dailyStocksX, self.requestEngine.dailyStocksY, marker=None, linestyle="-", color="r")
                self.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=6))

            self.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.2f"))
            self.ax.yaxis.set_minor_formatter(ticker.FormatStrFormatter("%.2f"))
            self.ax.tick_params(axis="y", which="major")
            self.ax.tick_params(axis="y", which="minor")
            self.fig.tight_layout()
            self.canvas.draw()
        if period == None:
            pass

        elif period == "monthly" and self.chosenStock is not None:
            self.requestEngine.getMonthlyStocks(self.chosenStock) # WHERE NOTHING THERE SHOULD BE STOCK SYHMBOL
            xStocks = self.requestEngine.dailyStocksX
            yStocks = self.requestEngine.dailyStocksY
            self.updateStocksTreeview()
            updateChart(period)

        elif period == "weekly" and self.chosenStock is not None:
            self.requestEngine.getWeeklyStocks(self.chosenStock)
            xStocks = self.requestEngine.dailyStocksX
            yStocks = self.requestEngine.dailyStocksY
            self.updateStocksTreeview()
            updateChart(period)

        elif period == "daily" and self.chosenStock is not None:
            self.requestEngine.getDailyStocks(self.chosenStock)
            xStocks = self.requestEngine.dailyStocksX
            yStocks = self.requestEngine.dailyStocksY
            self.updateStocksTreeview()
            updateChart(period)
        else:
            pass

    def updateStocksTreeview(self):
        def clearStocksTreeview():
            for row in self.stockTreeview.get_children():
                self.stockTreeview.delete(row)

        clearStocksTreeview()
        for index, day in enumerate(self.requestEngine.dailyStocksX):
            self.stockTreeview.insert("", "end", values=(day, self.requestEngine.dailyStocksY[index]))

    def initializeStockInfoFrame(self, stockAndChartFrame):
        stockInfoFrame = tk.LabelFrame(stockAndChartFrame, text="Informacje o akcjach")
        stockInfoFrame.grid(row=0, column=0, sticky='nsew')
        stockInfoFrame.grid_columnconfigure(0, weight=1)
        stockInfoFrame.grid_rowconfigure(0, weight=1)

        self.initializeStockWidgets(stockInfoFrame)
        
    def initializeStockWidgets(self, stockInfoFrame):
        # def updateStocks():
            # self.root.after()

        style = ttk.Style()
        style.configure("Treeview", rowheight=28)

        self.stockTreeview = ttk.Treeview(stockInfoFrame, columns=("Column 1", "Column 2"), show="headings")
        self.stockTreeview.grid(sticky='nsew')

        self.stockTreeview.heading("Column 1", text="Dzień")
        self.stockTreeview.heading("Column 2", text="Najwyż. wart.")

    def initializeCompanyInfoAndAnalystRecommendationsFrame(self):
        companyAndAnalystFrame = tk.Frame(self.root)
        companyAndAnalystFrame.grid(row=3, column=0, sticky='nsew')
        companyAndAnalystFrame.grid_columnconfigure(0, weight=1)
        companyAndAnalystFrame.grid_columnconfigure(1, weight=1)

        #distribute widgets equally
        companyAndAnalystFrame.grid_rowconfigure(0, weight=1)

        self.initializeCompanyInfoFrame(companyAndAnalystFrame)
        self.initializeAnalystRecommendationsFrame(companyAndAnalystFrame)

    def initializeCompanyInfoFrame(self, frame):
        companyInfoFrame = tk.LabelFrame(frame, text="Informacje o firmie: ")
        companyInfoFrame.grid(row=0, column=0, sticky='nsew')
        companyInfoFrame.grid_columnconfigure(0, weight=1)
        companyInfoFrame.grid_columnconfigure(1, weight=1)
        self.initializeCompanyInfoWidgets(companyInfoFrame)

    def initializeCompanyInfoWidgets(self, companyInfoFrame):
        self.companyName = tk.Label(companyInfoFrame, text="Nazwa:")
        self.companyName.grid(row=0, column=0, sticky='nsw')
        self.companySymbol = tk.Label(companyInfoFrame, text="Symbol:")
        self.companySymbol.grid(row=1, column=0, sticky='nsw')
        self.sectorName = tk.Label(companyInfoFrame, text="Sektor:")
        self.sectorName.grid(row=2, column=0, sticky='nsw')
        self.countryName = tk.Label(companyInfoFrame, text="Kraj firmy:")
        self.countryName.grid(row=3, column=0, sticky='nsw')
        self.addressName = tk.Label(companyInfoFrame, text="Adres:")
        self.addressName.grid(row=4, column=0, sticky='nsw')
        self.fiscalYearEnd = tk.Label(companyInfoFrame, text="Koniec roku fiskalnego")
        self.fiscalYearEnd.grid(row=5, column=0, sticky='nsw')

    def initializeAnalystRecommendationsFrame(self, frame):
        analystRecommendationsFrame = tk.LabelFrame(frame, text="Rekomendacje analityków")
        analystRecommendationsFrame.grid(row=0, column=1, columnspan=3, sticky='nsew')
        self.initializeAnalystRecommendationsWidgets(analystRecommendationsFrame)

    def initializeAnalystRecommendationsWidgets(self, analystRecommendationsFrame):
        self.targetPrice = tk.Label(analystRecommendationsFrame, text="Cena docelowa: ")
        self.targetPrice.grid(row=0, sticky="nsw")

        self.ratingStrongBuy = tk.Label(analystRecommendationsFrame, text="Zdecydowanie kupuj: ")
        self.ratingStrongBuy.grid(row=1, sticky="nsw")

        self.ratingBuy = tk.Label(analystRecommendationsFrame, text="Kupuj: ")
        self.ratingBuy.grid(row=2, sticky="nsw")

        self.ratingHold = tk.Label(analystRecommendationsFrame, text="Trzymaj: ")
        self.ratingHold.grid(row=3, sticky="nsw")

        self.ratingSell = tk.Label(analystRecommendationsFrame, text="Sprzedaj: ")
        self.ratingSell.grid(row=4, sticky="nsw")

    def openMonitorWindow(self):
        """ do weryfikacji jeszcze. Trzeba będzie podzielić to na mniejsze funkcje. Funkcja zwykle robi jedną i tylko jedną rzecz."""
        monitor_window = tk.Toplevel(self.root)
        monitor_window.title("Monitorowane akcje")
        monitor_window.geometry("600x400")

        # Sekcja tabeli monitorowanych akcji
        label_table = tk.Label(monitor_window, text="Monitorowane akcje:")
        label_table.pack(pady=5)

        columns = ("Akcja", "Kraj", "Alert", "Cena zakupu")

        # Tworzenie tabeli
        tree = ttk.Treeview(monitor_window, columns=columns, show='headings')

        # Nagłówki tabeli
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)

        # Dodanie przykładowych danych
        tree.insert("", tk.END, values=("INTC - Intel", "US", "Tak", "18.45$"))

        tree.pack(padx=10, pady=10)

if __name__ == "__main__":
    app = UserInterface()
