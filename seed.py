import os
import sys
from datetime import date, datetime, timedelta
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.donor import DonorProfile
from app.models.patient import PatientProfile
from app.models.hospital import Hospital
from app.models.blood_request import BloodRequest, EmergencyLevel, RequestStatus
from app.models.match import DonorMatch, MatchStatus
from app.models.inventory import BloodInventory
from app.models.donation import Donation
from app.models.notification import Notification
from app.auth import get_password_hash
from app.services.matching_service import run_donor_matching

def seed_database():
    print("[+] Initializing Blood Bridge Database Seed Script...")
    
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. Create Admin
        admin_user = User(
            name="System Admin",
            email="admin@bloodbridge.com",
            phone="+91 9876543210",
            password_hash=get_password_hash("Admin@123"),
            role=UserRole.ADMIN,
            is_verified=True,
            is_active=True
        )
        db.add(admin_user)
        print("  - Created Admin: admin@bloodbridge.com / Admin@123")

        # 2. Create Hospitals
        hospitals_data = [
            {
                "name": "Apollo City Hospital",
                "email": "apollo@hospital.com",
                "phone": "+91 1123456789",
                "address": "Mathura Road, Sarita Vihar",
                "city": "Delhi",
                "state": "Delhi",
                "pincode": "110076",
                "lat": 28.5355,
                "lng": 77.2882
            },
            {
                "name": "Fortis Healthcare Center",
                "email": "fortis@hospital.com",
                "phone": "+91 2234567890",
                "address": "Mulund Goregaon Link Rd",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400078",
                "lat": 19.1678,
                "lng": 72.9326
            },
            {
                "name": "Manipal Emergency Hospital",
                "email": "manipal@hospital.com",
                "phone": "+91 8034567891",
                "address": "HAL Old Airport Rd",
                "city": "Bangalore",
                "state": "Karnataka",
                "pincode": "560017",
                "lat": 12.9585,
                "lng": 77.6484
            },
            {
                "name": "Max Super Speciality Hospital",
                "email": "max@hospital.com",
                "phone": "+91 1145678901",
                "address": "Press Enclave Rd, Saket",
                "city": "Delhi",
                "state": "Delhi",
                "pincode": "110017",
                "lat": 28.5283,
                "lng": 77.2117
            },
            {
                "name": "Global Care Blood Bank",
                "email": "globalcare@hospital.com",
                "phone": "+91 4456789012",
                "address": "Perumbakkam Main Rd",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "pincode": "600100",
                "lat": 12.9010,
                "lng": 80.1914
            }
        ]

        hospitals_created = []
        bg_list = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

        for idx, h_data in enumerate(hospitals_data):
            h_user = User(
                name=h_data["name"],
                email=h_data["email"],
                phone=h_data["phone"],
                password_hash=get_password_hash("Hospital@123"),
                role=UserRole.HOSPITAL,
                is_verified=True,
                is_active=True
            )
            db.add(h_user)
            db.flush()

            h_profile = Hospital(
                user_id=h_user.id,
                name=h_data["name"],
                email=h_data["email"],
                phone=h_data["phone"],
                address=h_data["address"],
                city=h_data["city"],
                state=h_data["state"],
                pincode=h_data["pincode"],
                latitude=h_data["lat"],
                longitude=h_data["lng"],
                verified=True
            )
            db.add(h_profile)
            db.flush()
            hospitals_created.append(h_profile)

            for bg in bg_list:
                inv = BloodInventory(
                    hospital_id=h_profile.id,
                    blood_group=bg,
                    available_units=random.randint(5, 25),
                    reserved_units=random.randint(0, 4)
                )
                db.add(inv)

        print(f"  - Created {len(hospitals_created)} Hospitals with Blood Inventory Stock")

        # 3. Create 20 Sample Donors
        donor_names = [
            "Arun Kumar", "Priya Sharma", "Rahul Verma", "Ananya Deshmukh", "Vikram Singh",
            "Sneha Patel", "Rohan Mehta", "Kavita Reddy", "Amit Joshi", "Deepika Iyer",
            "Siddharth Rao", "Neha Gupta", "Karan Malhotra", "Pooja Roy", "Suresh Nair",
            "Ritu Saxena", "Manish Kapoor", "Divya Menon", "Aakash Choudhury", "Meera Bhatt"
        ]

        cities = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Delhi", "Delhi", "Mumbai", "Bangalore"]
        city_coords = {
            "Delhi": (28.6139, 77.2090),
            "Mumbai": (19.0760, 72.8777),
            "Bangalore": (12.9716, 77.5946),
            "Chennai": (13.0827, 80.2707)
        }

        donors_created = []
        for i, name in enumerate(donor_names):
            email = f"donor{i+1}@bloodbridge.com"
            bg = bg_list[i % len(bg_list)]
            city = cities[i % len(cities)]
            base_lat, base_lng = city_coords[city]
            lat = base_lat + random.uniform(-0.08, 0.08)
            lng = base_lng + random.uniform(-0.08, 0.08)

            d_user = User(
                name=name,
                email=email,
                phone=f"+91 9810{i:06d}",
                password_hash=get_password_hash("Donor@123"),
                role=UserRole.DONOR,
                is_verified=True,
                is_active=True
            )
            db.add(d_user)
            db.flush()

            days_ago = random.choice([30, 45, 100, 120, 150, 200])
            last_date = date.today() - timedelta(days=days_ago)

            d_profile = DonorProfile(
                user_id=d_user.id,
                blood_group=bg,
                date_of_birth=date(1992, (i%12)+1, (i%28)+1),
                gender="Male" if i % 2 == 0 else "Female",
                address=f"Street {i+1}, Sector {i+5}",
                city=city,
                state=city,
                pincode=f"1100{i:02d}",
                latitude=round(lat, 5),
                longitude=round(lng, 5),
                available=True if i % 5 != 0 else False,
                last_donation_date=last_date,
                total_donations=random.randint(1, 15),
                successful_donations=random.randint(1, 12)
            )
            db.add(d_profile)
            db.flush()
            donors_created.append(d_profile)

        print(f"  - Created {len(donors_created)} Sample Donors across various blood groups & cities")

        # 4. Create 10 Sample Patients
        patient_names = [
            "Rajesh Khanna", "Sunita Agarwal", "Tarun Bhasin", "Sunil Fernandez", "Monika Sen",
            "Alok Misra", "Bhavna Bose", "Gaurav Trivedi", "Harish Kumar", "Ishita Dutta"
        ]

        patients_created = []
        for i, name in enumerate(patient_names):
            email = f"patient{i+1}@bloodbridge.com"
            bg = bg_list[i % len(bg_list)]
            city = cities[i % len(cities)]

            p_user = User(
                name=name,
                email=email,
                phone=f"+91 9910{i:06d}",
                password_hash=get_password_hash("Patient@123"),
                role=UserRole.PATIENT,
                is_verified=True,
                is_active=True
            )
            db.add(p_user)
            db.flush()

            p_profile = PatientProfile(
                user_id=p_user.id,
                blood_group=bg,
                date_of_birth=date(1985, (i%12)+1, (i%28)+1),
                gender="Male" if i % 2 == 0 else "Female",
                address=f"Apartment {i+10}, Phase {i+1}",
                city=city,
                state=city,
                pincode=f"1100{i:02d}"
            )
            db.add(p_profile)
            db.flush()
            patients_created.append(p_profile)

        print(f"  - Created {len(patients_created)} Sample Patients")

        # 5. Create Sample Blood Requests
        sample_requests_data = [
            {
                "patient_idx": 0,
                "blood_group": "O+",
                "units": 3,
                "hospital": hospitals_created[0],
                "emergency": EmergencyLevel.CRITICAL,
                "notes": "Emergency surgery required. High priority."
            },
            {
                "patient_idx": 1,
                "blood_group": "A-",
                "units": 2,
                "hospital": hospitals_created[1],
                "emergency": EmergencyLevel.HIGH,
                "notes": "Required for scheduled procedure tomorrow morning."
            },
            {
                "patient_idx": 2,
                "blood_group": "B+",
                "units": 1,
                "hospital": hospitals_created[2],
                "emergency": EmergencyLevel.MEDIUM,
                "notes": "Routine transfusion needed."
            },
            {
                "patient_idx": 3,
                "blood_group": "AB+",
                "units": 2,
                "hospital": hospitals_created[3],
                "emergency": EmergencyLevel.CRITICAL,
                "notes": "ICU urgent requirement."
            },
            {
                "patient_idx": 4,
                "blood_group": "O-",
                "units": 4,
                "hospital": hospitals_created[0],
                "emergency": EmergencyLevel.CRITICAL,
                "notes": "Universal donor needed urgently for accident trauma."
            }
        ]

        requests_created = []
        for r_data in sample_requests_data:
            patient = patients_created[r_data["patient_idx"]]
            hosp = r_data["hospital"]
            
            req = BloodRequest(
                patient_id=patient.id,
                hospital_id=hosp.id,
                hospital_name=hosp.name,
                hospital_address=hosp.address,
                city=hosp.city,
                state=hosp.state,
                blood_group=r_data["blood_group"],
                units_required=r_data["units"],
                emergency_level=r_data["emergency"],
                latitude=hosp.latitude,
                longitude=hosp.longitude,
                required_date=date.today().strftime("%Y-%m-%d"),
                required_time="14:00",
                status=RequestStatus.SEARCHING,
                notes=r_data["notes"]
            )
            db.add(req)
            db.flush()
            requests_created.append(req)

            matches = run_donor_matching(db, req)
            
            notif = Notification(
                user_id=patient.user_id,
                request_id=req.id,
                title="Blood Request Broadcast Active",
                message=f"Your request for {req.units_required} unit(s) of {req.blood_group} blood has matched {len(matches)} eligible donor(s).",
                type="REQUEST_NEW",
                is_read=False
            )
            db.add(notif)

        print(f"  - Created {len(requests_created)} Blood Requests and ran Matching Engine for initial matches")

        db.commit()
        print("\n[SUCCESS] DATABASE SEED COMPLETE! All initial data successfully populated.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database Seed Failed: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
