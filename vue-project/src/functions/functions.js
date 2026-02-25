/* This is a descending sort with newest items at the top and oldest at the bottom */
export const sort = (list) => {
    const sort_by_years = () => {
        list.sort((b, a) => {
            return parseInt(a.date.split("/")[2]) - parseInt(b.date.split("/")[2])
        })
    }

    sort_by_years();

    let years = [[]]
    const sort_by_months = () => {
        let temp_year = 0
        for (let i = 0, j = 0, curr_year = 0; i < list.length; i++) {
            if (i == 0) {
                curr_year = parseInt(list[0].date.split("/")[2])
                years[0].push(list[0])
            }
            else {
                temp_year = parseInt(list[i].date.split("/")[2])
                if (temp_year == curr_year) years[j].push(list[i])
                else {
                    curr_year = temp_year;
                    years.push([])
                    j += 1
                    years[j].push(list[i])
                }
            }
        }

        for (let year of years)
            year.sort((b, a) => {
                return parseInt(a.date.split("/")[0]) - parseInt(b.date.split("/")[0])
            })
    }

    sort_by_months();

    const sort_by_days = () => {
        let ret_list = []
        for (let year of years) {
            let months = [[]]
            let temp_month = 0
            for (let i = 0, j = 0, curr_month = 0; i < year.length; i++) {
                if (i == 0) {
                    curr_month = parseInt(year[0].date.split("/")[0])
                    months[0].push(year[0])
                }
                else {
                    temp_month = parseInt(year[i].date.split("/")[0])
                    if (temp_month == curr_month) months[j].push(year[i])
                    else {
                        curr_month = temp_month;
                        months.push([])
                        j += 1
                        months[j].push(year[i])
                    }
                }
            }

            for (let month of months)
                month.sort((b, a) => {
                    return parseInt(a.date.split("/")[1]) - parseInt(b.date.split("/")[1])
                })

            for (let month of months)
                for (let item of month)
                    ret_list.push(item);
        }
        return ret_list;
    }
    return sort_by_days()
}

import { ref } from 'vue'

export const initials = ref('')

export const setInitials = (fullName) => {
    let result = ''
    const name_array = fullName && fullName.trim() && fullName.split(" ").filter(Boolean)

    if (name_array && name_array.length > 1) result = name_array[0][0] + name_array[1][0]
    else if (name_array && name_array[0].length > 1) result = name_array[0][0] + name_array[0][1]
    else if (name_array && name_array[0].length === 1) result = name_array[0][0]

    initials.value = result.toUpperCase()
}
 
export const monthly_revenue = (list, num_of_columns) => {
    const split_into_months = (list) => {
        let years = [[]]
        const sort_by_months = () => {
            let temp_year = 0
            for (let i = 0, j = 0, curr_year = 0; i < list.length; i++) {
                if (i == 0) {
                    curr_year = parseInt(list[0].date.split("/")[2])
                    years[0].push(list[0])
                }
                else {
                    temp_year = parseInt(list[i].date.split("/")[2])
                    if (temp_year == curr_year) years[j].push(list[i])
                    else {
                        curr_year = temp_year;
                        years.push([])
                        j += 1
                        years[j].push(list[i])
                    }
                }
            }
        }
    
        const sort_by_days = () => {
            let ret_list = []
            let i = 0;
            for (let year of years) {
                let months = [[]]
                let temp_month = 0
                for (let i = 0, j = 0, curr_month = 0; i < year.length; i++) {
                    if (i == 0) {
                        curr_month = parseInt(year[0].date.split("/")[0])
                        months[0].push(year[0])
                    }
                    else {
                        temp_month = parseInt(year[i].date.split("/")[0])
                        if (temp_month == curr_month) months[j].push(year[i])
                        else {
                            curr_month = temp_month;
                            months.push([])
                            j += 1
                            months[j].push(year[i])
                        }
                    }
                }
                for (let month of months) {
                    ret_list.push([])
                    for (let item of month)
                        ret_list[i].push(item);
                    i++;
                }
            }
            return ret_list
        }
        sort_by_months()
        return sort_by_days()
    
    }

    const getLabel = (date) => {
        let dateArray = date.split("/")
        return dict[dateArray[0]] + " '" + dateArray[2];
    }

    const dict = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"};

    const newList = split_into_months(list)
    let retList = []
    let label = null;
    let total = 0;

    for (let i = newList.length - 1, j = 0; i >= 0 && j < num_of_columns; i--, j++) {
        label = null;
        total = 0
        for (let item of newList[i]) {
            if (!label) {
                label = getLabel(item.date);
            }
            total += parseFloat(item.price);
        }
        retList.push({label: label, price: total})
    }

    return retList.reverse();
}

export const top_revenues = (list, num_of_items) => {
    let total = 0
    for (let item of list) total += parseFloat(item.price)
    list.sort((b, a) => a.price - b.price);
    let newList = list.slice(0, num_of_items)
    for (let item of newList) total -= parseFloat(item.price)
    newList.push({date: "Other", price: total})
    return newList
}

export const backgroundColors = ['rgb(21, 22, 24)', 'rgb(85, 85, 34)', 'rgb(169, 164, 84)', 'rgb(176, 121, 70)', 'rgb(145, 85, 61)', 'rgb(239, 228, 212)'];
export const darkBackgroundColors = ['rgb(255, 203, 165)', 'rgb(85, 85, 34)', 'rgb(169, 164, 84)', 'rgb(176, 121, 70)', 'rgb(145, 85, 61)', 'rgb(239, 228, 212)'];

export const getAverage = (list) => {

    if (list.length < 1) return 0

    let retVal = 0

    for (let item of list) retVal += parseFloat(item.price)

    return parseFloat((retVal / list.length)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}