function showTab(tabName) {
    document.querySelectorAll('.form-section').forEach(section => section.classList.remove('active'));
    document.querySelectorAll('.tab-selector button').forEach(button => button.classList.remove('active'));
    document.getElementById('form-' + tabName).classList.add('active');
    document.getElementById('tab-' + tabName).classList.add('active');
}

let childrenMap = {};
const parentSelect = document.getElementById('parent_category');
const subCategoryWrapper = document.getElementById('sub_category_wrapper');
const subCategorySelect = document.getElementById('sub_category');
const finalCategoryIdInput = document.getElementById('category_id');
parentSelect.addEventListener('change', function() {
    const selectedParentId = this.value;
    const children = childrenMap[selectedParentId];
    finalCategoryIdInput.value = selectedParentId;
    subCategorySelect.innerHTML = '';
    if (children && children.length > 0) {
        const defaultOption = document.createElement('option');
        defaultOption.value = selectedParentId;
        defaultOption.textContent = `-- Select Sub-Category (or use Parent) --`;
        subCategorySelect.appendChild(defaultOption);
        children.forEach(child => {
            const option = document.createElement('option');
            option.value = child.id;
            option.textContent = child.name;
            subCategorySelect.appendChild(option);
        });
        subCategoryWrapper.classList.remove('hidden');
    } else {
        subCategoryWrapper.classList.add('hidden');
    }
});
subCategorySelect.addEventListener('change', function() { if(this.value) { finalCategoryIdInput.value = this.value; } });

async function setType(type) {
    document.getElementById('type').value = type;
    document.getElementById('expense-btn').classList.toggle('active', type === 'expense');
    document.getElementById('income-btn').classList.toggle('active', type === 'income');
    document.getElementById('transfer-btn').classList.toggle('active', type === 'transfer');
    const descriptionWrapper = document.getElementById('description_wrapper');
    const categoryWrapper = document.getElementById('category_fields_wrapper');
    const pillarWrapper = document.getElementById('pillar_field_wrapper');
    const fromAccountLabel = document.getElementById('from_account_label');
    const toAccountWrapper = document.getElementById('to_account_wrapper');
    const descriptionInput = document.getElementById('description');
    const parentCategoryInput = document.getElementById('parent_category');
    const pillarInput = document.getElementById('pillar_id');
    const toAccountInput = document.getElementById('to_account_id');
    if (type === 'transfer') {
        descriptionWrapper.classList.add('hidden');
        categoryWrapper.classList.add('hidden');
        pillarWrapper.classList.add('hidden');
        toAccountWrapper.classList.remove('hidden');
        fromAccountLabel.textContent = 'From Account';
        descriptionInput.required = false;
        parentCategoryInput.required = false;
        pillarInput.required = false;
        toAccountInput.required = true;
    } else {
        descriptionWrapper.classList.remove('hidden');
        categoryWrapper.classList.remove('hidden');
        pillarWrapper.classList.remove('hidden');
        toAccountWrapper.classList.add('hidden');
        fromAccountLabel.textContent = 'Account';
        descriptionInput.required = true;
        parentCategoryInput.required = true;
        pillarInput.required = true;
        toAccountInput.required = false;
        try {
            const response = await fetch(`/api/categories/${type}`);
            const data = await response.json();
            childrenMap = data.children_map;
            parentSelect.innerHTML = '<option value="" disabled selected>-- Select a Parent --</option>';
            subCategoryWrapper.classList.add('hidden');
            subCategorySelect.innerHTML = '';
            finalCategoryIdInput.value = '';
            data.parents.forEach(parent => {
                const option = document.createElement('option');
                option.value = parent.id;
                option.textContent = parent.name;
                parentSelect.appendChild(option);
            });
        } catch (error) { console.error('Failed to fetch categories:', error); }
    }
}

const actionSelect = document.getElementById('inv_action');
const tradingWrapper = document.getElementById('trading_fields_wrapper');
const conversionWrapper = document.getElementById('conversion_fields_wrapper');
const tickerWrapper = document.getElementById('ticker_field_wrapper');
const quantityWrapper = document.getElementById('quantity_field_wrapper');
const feesWrapper = document.getElementById('fees_field_wrapper');
const invTicker = document.getElementById('inv_ticker');
const invPrice = document.getElementById('inv_price');
const invFromAmount = document.getElementById('inv_from_amount');
const invToAmount = document.getElementById('inv_to_amount');
const invConversionRate = document.getElementById('inv_conversion_rate');
const invConversionFee = document.getElementById('inv_conversion_fee');
const invAccount = document.getElementById('inv_account');
const invFromCurrency = document.getElementById('inv_from_currency');
const invToCurrency = document.getElementById('inv_to_currency');

function handleActionChange() {
    const action = actionSelect.value;
    const priceLabel = document.querySelector('label[for="inv_price"]');
    const tickerLabel = document.querySelector('label[for="inv_ticker"]');
    tradingWrapper.classList.add('hidden');
    conversionWrapper.classList.add('hidden');
    invTicker.required = false;
    invPrice.required = false;
    invFromAmount.required = false;
    invToAmount.required = false;
    if (action === 'Money Conversion') {
        conversionWrapper.classList.remove('hidden');
        invFromAmount.required = true;
        invToAmount.required = true;
    } else {
        tradingWrapper.classList.remove('hidden');
        invPrice.required = true;
        switch (action) {
            case 'Buy':
            case 'Sell':
                tickerWrapper.classList.remove('hidden');
                quantityWrapper.classList.remove('hidden');
                feesWrapper.classList.remove('hidden');
                tickerLabel.textContent = 'Ticker';
                priceLabel.textContent = 'Price Per Share USD';
                invTicker.required = true;
                break;
            case 'Deposit':
            case 'Withdrawal':
                tickerWrapper.classList.add('hidden');
                quantityWrapper.classList.add('hidden');
                feesWrapper.classList.add('hidden');
                priceLabel.textContent = 'Amount USD';
                break;
            case 'Dividend':
                tickerWrapper.classList.remove('hidden');
                quantityWrapper.classList.add('hidden');
                feesWrapper.classList.add('hidden');
                tickerLabel.textContent = 'Ticker';
                priceLabel.textContent = 'Dividend Amount USD';
                invTicker.required = true;
                break;
            case 'Fee/Expense':
                tickerWrapper.classList.remove('hidden');
                quantityWrapper.classList.add('hidden');
                feesWrapper.classList.add('hidden');
                tickerLabel.textContent = 'Description';
                priceLabel.textContent = 'Expense Amount USD';
                invTicker.required = true;
                break;
        }
    }
}

function calculateConversionDetails() {
    const fromAmount = parseFloat(invFromAmount.value);
    const toAmount = parseFloat(invToAmount.value);
    const accountName = invAccount.options[invAccount.selectedIndex].text;
    const fromCurrency = invFromCurrency.value;
    const toCurrency = invToCurrency.value;
    let rate = 0;
    if (fromAmount > 0 && toAmount > 0) {
        rate = toAmount / fromAmount;
        invConversionRate.value = rate.toFixed(6);
    }
    if (accountName.includes("IBKR") && fromCurrency === 'ILS' && toCurrency === 'USD' && rate > 0) {
        const feeInUSD = 10 / rate;
        invConversionFee.value = feeInUSD.toFixed(2);
    }
}

actionSelect.addEventListener('change', handleActionChange);
invFromAmount.addEventListener('input', calculateConversionDetails);
invToAmount.addEventListener('input', calculateConversionDetails);
invAccount.addEventListener('change', calculateConversionDetails);
invFromCurrency.addEventListener('change', calculateConversionDetails);
invToCurrency.addEventListener('change', calculateConversionDetails);

document.addEventListener('DOMContentLoaded', function() {
    setType('expense');
    showTab('expense');
    handleActionChange();
});
