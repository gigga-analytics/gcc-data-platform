
-- General Ledger Accounts
CREATE TABLE GL_Accounts (
    AccountCode VARCHAR(20) PRIMARY KEY,
    AccountName VARCHAR(100),
    AccountType VARCHAR(50) -- Asset, Liability, Equity, Revenue, Expense
);

-- Cost Centers
CREATE TABLE CostCenters (
    CostCenterID VARCHAR(20) PRIMARY KEY,
    Name VARCHAR(100),
    Department VARCHAR(100),
    Manager VARCHAR(100),
    Region VARCHAR(50)
);

-- General Ledger Transactions
CREATE TABLE GL_Transactions (
    TransactionID VARCHAR(30) PRIMARY KEY,
    Date DATE,
    AccountCode VARCHAR(20),
    Debit DECIMAL(18,2),
    Credit DECIMAL(18,2),
    Currency VARCHAR(10),
    CostCenterID VARCHAR(20),
    CompanyCode VARCHAR(20),
    JournalEntryType VARCHAR(50),
    FOREIGN KEY (AccountCode) REFERENCES GL_Accounts(AccountCode),
    FOREIGN KEY (CostCenterID) REFERENCES CostCenters(CostCenterID)
);

-- GL Cost Center Split
CREATE TABLE GL_CostCenterSplit (
    SplitID VARCHAR(30) PRIMARY KEY,
    TransactionID VARCHAR(30),
    CostCenterID VARCHAR(20),
    AllocatedAmount DECIMAL(18,2),
    FOREIGN KEY (TransactionID) REFERENCES GL_Transactions(TransactionID),
    FOREIGN KEY (CostCenterID) REFERENCES CostCenters(CostCenterID)
);

-- Vendors
CREATE TABLE Vendors (
    VendorID VARCHAR(20) PRIMARY KEY,
    Name VARCHAR(100),
    Country VARCHAR(50),
    Industry VARCHAR(50),
    BankDetails VARCHAR(200)
);

-- Vendor Invoices
CREATE TABLE VendorInvoices (
    InvoiceID VARCHAR(30) PRIMARY KEY,
    VendorID VARCHAR(20),
    InvoiceDate DATE,
    DueDate DATE,
    Amount DECIMAL(18,2),
    Tax DECIMAL(18,2),
    Currency VARCHAR(10),
    PaymentStatus VARCHAR(20),
    FOREIGN KEY (VendorID) REFERENCES Vendors(VendorID)
);

-- Customers
CREATE TABLE Customers (
    CustomerID VARCHAR(20) PRIMARY KEY,
    CustomerName VARCHAR(100),
    Industry VARCHAR(50),
    Region VARCHAR(50),
    AccountManager VARCHAR(100)
);

-- Customer Invoices
CREATE TABLE CustomerInvoices (
    InvoiceID VARCHAR(30) PRIMARY KEY,
    CustomerID VARCHAR(20),
    InvoiceDate DATE,
    DueDate DATE,
    Amount DECIMAL(18,2),
    Tax DECIMAL(18,2),
    PaymentStatus VARCHAR(20),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
);

-- Budget Plans
CREATE TABLE BudgetPlans (
    BudgetID VARCHAR(30) PRIMARY KEY,
    AccountCode VARCHAR(20),
    CostCenterID VARCHAR(20),
    FiscalYear INT,
    Month INT,
    PlannedAmount DECIMAL(18,2),
    FOREIGN KEY (AccountCode) REFERENCES GL_Accounts(AccountCode),
    FOREIGN KEY (CostCenterID) REFERENCES CostCenters(CostCenterID)
);

-- Forecasts
CREATE TABLE Forecasts (
    ForecastID VARCHAR(30) PRIMARY KEY,
    Scenario VARCHAR(50),
    AccountCode VARCHAR(20),
    FiscalYear INT,
    Month INT,
    ForecastedAmount DECIMAL(18,2),
    FOREIGN KEY (AccountCode) REFERENCES GL_Accounts(AccountCode)
);

-- Employee Salaries
CREATE TABLE EmployeeSalaries (
    SalaryID VARCHAR(30) PRIMARY KEY,
    EmployeeID VARCHAR(20),
    CostCenterID VARCHAR(20),
    GrossSalary DECIMAL(18,2),
    Taxes DECIMAL(18,2),
    Bonuses DECIMAL(18,2),
    Month DATE,
    Currency VARCHAR(10),
    FOREIGN KEY (CostCenterID) REFERENCES CostCenters(CostCenterID)
);

-- Asset Registry
CREATE TABLE AssetRegistry (
    AssetID VARCHAR(30) PRIMARY KEY,
    Description VARCHAR(200),
    PurchaseDate DATE,
    OriginalCost DECIMAL(18,2),
    DepreciationMethod VARCHAR(50),
    DepreciationRate DECIMAL(5,2),
    NetBookValue DECIMAL(18,2),
    CostCenterID VARCHAR(20),
    FOREIGN KEY (CostCenterID) REFERENCES CostCenters(CostCenterID)
);

-- Bank Transactions
CREATE TABLE BankTransactions (
    TransactionID VARCHAR(30) PRIMARY KEY,
    BankAccount VARCHAR(50),
    Date DATE,
    Amount DECIMAL(18,2),
    TransactionType VARCHAR(20), -- inflow/outflow
    Description VARCHAR(200),
    Currency VARCHAR(10)
);
