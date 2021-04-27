ACTIVE_DISTRCT_LIST_URL = "https://life-api.coronasafe.network/data/active_district_data.json"
AMBULANCE_AVAILABILITY_URL = "https://life-api.coronasafe.network/data/ambulance.json"
HELPLINE_NUMBERS_URL = "https://life-api.coronasafe.network/data/helpline.json"
HOSPITALS_AND_BEDS_URL = "https://life-api.coronasafe.network/data/hospital_clinic_centre.json"
MEDICINE_AVAILABILITY_URL = "https://life-api.coronasafe.network/data/medicine.json"
OXYGEN_AVAILABILITY_URL = "https://life-api.coronasafe.network/data/oxygen.json"

SERVICE_URL_MAP = {
    "ambulances" : AMBULANCE_AVAILABILITY_URL,
    "ambulance" : AMBULANCE_AVAILABILITY_URL,
    "helpline number" : HELPLINE_NUMBERS_URL,
    "helpline" : HELPLINE_NUMBERS_URL,
    "hospitals" : HOSPITALS_AND_BEDS_URL,
    "hospital" : HOSPITALS_AND_BEDS_URL,
    "beds" : HOSPITALS_AND_BEDS_URL,
    "bed" : HOSPITALS_AND_BEDS_URL,
    "hospital beds" : HOSPITALS_AND_BEDS_URL,
    "medicines": MEDICINE_AVAILABILITY_URL,
    "medicine": MEDICINE_AVAILABILITY_URL,
    "oxygen": OXYGEN_AVAILABILITY_URL
}