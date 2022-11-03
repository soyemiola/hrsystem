
def getband(taxable, gross):
    get_first = band(taxable, 300000, 7, band=1)
    firstband = get_first['Band']
    secondtaxable = get_first['NextTaxable']

    get_second = band(secondtaxable, 300000, 11, band=2)
    secondband = get_second['Band']
    thirdtaxable = get_second['NextTaxable']

    get_third = band(thirdtaxable, 500000, 15, band=3)
    thirdband = get_third['Band']
    fourthtaxable = get_third['NextTaxable']

    get_fourth = band(fourthtaxable, 500000, 19, band=4)
    fourthband = get_fourth['Band']
    fifthtaxable = get_fourth['NextTaxable']

    get_fifth = band(fifthtaxable, 1600000, 21, band=5) 
    fifthband = get_fifth['Band']
    sixthtaxable = get_fifth['NextTaxable']

    get_sixth = band(sixthtaxable, 3200000, 24, band=6) 
    sixthband = get_sixth['Band']
    lastband = get_sixth['NextTaxable']

    first_ = '{:,.2f}'.format(firstband)
    second_ = '{:,.2f}'.format(secondband)
    third_ = '{:,.2f}'.format(thirdband)
    fourth_ = '{:,.2f}'.format(fourthband)
    fifth_ = '{:,.2f}'.format(fifthband)
    sixth_ = '{:,.2f}'.format(sixthband)

    emp_total_tax = total_tax(firstband, secondband, thirdband, fourthband, fifthband, sixthband)
    emp_minimum_tax = minimum_tax(1, gross)
    emp_higherMinimum_tax = higher_minimum_tax(emp_total_tax, emp_minimum_tax)
    emp_effective_tax = effective_tax(emp_higherMinimum_tax, gross)

    res = {
        "Firstband": first_,
        "Secondband": second_,
        "Thirdband": third_,
        "Fourthband": fourth_,
        "Fifthband": fifth_,
        "Sixthband": sixth_,
        "Total_tax": emp_total_tax,
        "Minimum_tax": emp_minimum_tax,
        "HM_tax": emp_higherMinimum_tax,
        "Effective_tax": emp_effective_tax
    }
    return res

    
def _get_percentage_value(get_percentage):
    result = 100 / get_percentage
    return result


def band(taxable, value, value_percentage, band):
    if band == 6:
        #value = taxable
        next_taxable = taxable
    else:
        next_taxable = taxable - value 

    

    if next_taxable > value: 
        tax_value = _get_percentage(value_percentage, value)
        if tax_value > 0:
            res = {
                "Band": tax_value,
                "NextTaxable": next_taxable
            }
            return res
        else:
            res = {
                "Band": 0,
                "NextTaxable": 0
            }
            return res
    elif taxable < value:
        tax_value = _get_percentage(value_percentage, taxable)
        if tax_value > 0:
            res = {
                "Band": tax_value,
                "NextTaxable": next_taxable
            }
            return res
        else:
            res = {
                "Band": 0,
                "NextTaxable": 0
            }
            return res
    else:
        tax_value = _get_percentage(value_percentage, value)
        res = {
            "Band": tax_value,
            "NextTaxable": next_taxable
        }
        return res


def _get_percentage(get_percentage, get_amount):
    stp1 = get_percentage / 100
    stp2 = stp1 * get_amount
    return stp2


def total_tax(first_band, second_band, third_band, forth_band, fifth_band, sixth_band):
    _total_tax = (first_band, second_band, third_band, forth_band, fifth_band, sixth_band)
    _sum_of_total_tax = sum(_total_tax)
    return _sum_of_total_tax


def minimum_tax(get_percentage_value, get_gross_pay):
    get_per = _get_percentage_value(get_percentage_value)
    getresult = get_gross_pay / get_per
    return getresult


def higher_minimum_tax(get_total_tax, get_minimum_tax):
    if get_total_tax > get_minimum_tax:
        return get_total_tax
    else:
        return get_minimum_tax


def effective_tax(get_H_M, get_gross_pay):
    rtn_effective_tax = get_H_M / get_gross_pay
    return rtn_effective_tax
