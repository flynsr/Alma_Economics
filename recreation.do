clear all

	set more off
	cd "/Users/flynscott-reilly/Documents/Jobs/Alma Economics/Scotland Paper Recreation/Stata"
	
	
	*---------- Creating Postcode Sample ---------*
	
	use "smalluser.dta", clear
	drop if !missing(dateofdeletion)
	keep postcode postcodesector
	bys postcodesector: sample 1,count
	keep postcode
	export delimited using "PostcodeSample.csv", novarnames replace
	
	
	*--------- Population Density Dataset ---------*
	
	use "smalluser.dta", clear
	drop if !missing(dateofdeletion)
	rename outputarea2022code code
	merge m:m code using "densitybypostcode.dta"
	keep if _merge==3
	keep postcodesector population area
	duplicates drop
	
	bys postcodesector: egen poptotal=sum(population)
	bys postcodesector: egen areatotal=sum(area)
	gen density = poptotal/areatotal
	keep postcodesector density 
	duplicates drop
	save "popdensity.dta", replace
	
	*--------- Postcode Characteristics ---------*
	
	use "smalluser.dta", clear
	drop if !missing(dateofdeletion)
	keep postcode postcodesector islandcode urbanrural6fold2020code urbanrural8fold2020code nuts318nm nuts218nm
	merge m:m postcodesector using "popdensity.dta"
	drop _merge
	rename nuts218nm nuts2
	rename nuts318nm nuts3

	*Urban-Rural code conversion*
	
	gen UR3 = 1 if urbanrural6fold2020code <= 4
	replace UR3 = 2 if urbanrural6fold2020code == 5
	replace UR3 = 3 if urbanrural6fold2020code == 6
	rename urbanrural8fold2020code UR8
	drop urbanrural6fold2020code
	
	*Generating Dummy Variables*
	tab UR8, gen(UR8)
	tab UR3, gen(UR3)
	gen nutsE = (nuts2 == "Eastern Scotland")
	gen nutsHI =(nuts2 == "Highlands and Islands")
	gen nutsNE = (nuts2 == "North Eastern Scotland")
	gen nutsS = (nuts2 == "Southern Scotland")
	gen nutsWC = (nuts2 == "West Central Scotland")
	
	order postcode postcodesector islandcode UR3 UR8 nuts2 nuts3 density
	save "postcodecharacteristics.dta", replace
	
	
	*------------ Merging Quote Datasets -----------*
	
	use "dpdquotes.dta", clear
	gen yodel =.
	gen parcelforce=.
	
	append using "parcelforcequotes.dta"
	append using "yodelquotes.dta"
	
	replace dpd=0 if missing(dpd)
	replace yodel=0 if missing(yodel)
	replace parcelforce=0 if missing(parcelforce)
	
	rename stddropoff quote_stddropoff
	rename ndddropoff quote_ndddropoff
	rename stdd2d quote_stdd2d
	rename nddd2d quote_nddd2d
	
	*Reshaping dataset*
	
	gen id = _n
	reshape long quote_, i(id) j(delivery_type) string
	drop if missing(quote_)
	drop id
	rename quote_ quote
	
	*Generating dummy variables*
	
	gen large = (parcelsize == "large")
	gen medium = (parcelsize == "medium")
	gen door_to_door = inlist(delivery_type, "stdd2d", "nddd2d")
	gen next_day = inlist(delivery_type, "ndddropoff", "nddd2d")  
	
	keep deliverypostcode quote medium large door_to_door next_day dpd parcelforce yodel
	order deliverypostcode quote medium large door_to_door next_day dpd parcelforce yodel
	
	save "quotes.dta", replace

	*--------- Constructing Final Dataset ---------*
	
	use "quotes.dta", clear
	rename deliverypostcode postcode
	merge m:m postcode using "postcodecharacteristics.dta"
	keep if _merge == 3
	drop _merge
	
	gen logquote = ln(quote)
	gen logdensity = ln(density)
	
	save "regression.dta", replace
	

	*----------------- Regressions ----------------*
	
	eststo clear
	eststo: reg logquote logdensity door_to_door next_day UR32 UR33 large medium dpd parcelforce yodel
	eststo: reg logquote door_to_door next_day large medium UR82 UR83 UR84 UR85 UR86 UR87 UR88 dpd parcelforce yodel
	eststo: reg logquote logdensity door_to_door next_day large medium islandcode dpd parcelforce yodel
	eststo: reg logquote logdensity door_to_door next_day large medium nutsE nutsHI nutsNE nutsWC dpd parcelforce yodel
	
	esttab using tableD1.rtf, replace label nogap b(%9.2f) t(%9.2f) star(* 0.05 ** 0.01 *** 0.001) ///
	mtitles("Delivery price" "Delivery price" "Delivery price" "Delivery price") stats(N r2)  compress ///
	varlabels(logdensity "Population density" door_to_door "Door-to-door delivery" next_day "Next-day delivery" ///
	UR32 "Accessible Rural (UR3)" UR33 "Remote Rural (UR3)" large "Large parcels" medium "Medium parcels" ///
	UR82 "Other urban areas (UR8)" UR83 "Accessible small towns (UR8)" UR84 "Remote small towns (UR8)" ///
	UR85 "Very remote small towns (UR8)" UR86 "Accessible rural (UR8)" UR87 "Remote rural (UR8)" ///
	UR88 "Very remote rural (UR8)" islandcode "Island" nutsE "Eastern Scotland" nutsHI "Highlands and Islands" ///
	nutsNE "North Eastern Scotland" nutsWC "West Central Scotland" _cons "Constant") drop(dpd yodel parcelforce)
	
	
	
	
