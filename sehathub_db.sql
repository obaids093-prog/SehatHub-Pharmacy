-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Oct 16, 2026 at 05:31 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `sehathub_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `admins`
--

CREATE TABLE `admins` (
  `admin_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `permission_level` enum('super_admin','manager') DEFAULT 'manager'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admins`
--

INSERT INTO `admins` (`admin_id`, `user_id`, `permission_level`) VALUES
(2, 14, 'super_admin');

-- --------------------------------------------------------

--
-- Table structure for table `audit_logs`
--

CREATE TABLE `audit_logs` (
  `log_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `action_type` varchar(100) NOT NULL,
  `description` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `audit_logs`
--

INSERT INTO `audit_logs` (`log_id`, `user_id`, `action_type`, `description`, `created_at`) VALUES
(1, 10, 'STOCK_UPDATE', 'Tonoflex-P Tablets (20 Tablets) — stock changed from 25 to 38', '2026-08-03 17:03:39'),
(2, 10, 'VARIANT_UPDATE', 'Accu-Chek Instant S (1 Unit) — price Rs. 3349.00 → Rs. 3449.0, stock 49 → 25', '2026-08-03 17:04:18'),
(3, 10, 'VARIANT_UPDATE', 'Accu-Chek Instant S (1 Unit) — size=1 Unit, price=3449.0, stock=25', '2026-08-03 17:04:26'),
(4, 10, 'PRESCRIPTION_REJECTED', 'Pharmacist rejected prescription #18', '2026-10-16 15:16:03'),
(5, 10, 'ORDER_CONFIRMED', 'Pharmacist updated order #33 status to confirmed', '2026-10-16 15:19:05'),
(6, 10, 'ORDER_PACKED', 'Pharmacist updated order #33 status to packed', '2026-10-16 15:19:12');

-- --------------------------------------------------------

--
-- Table structure for table `brands`
--

CREATE TABLE `brands` (
  `brand_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `brands`
--

INSERT INTO `brands` (`brand_id`, `name`) VALUES
(2, 'Abbott'),
(30, 'Adidas'),
(24, 'AGP'),
(21, 'ATCO Laboratories'),
(13, 'Barrett Hodgson'),
(17, 'Bayer'),
(27, 'believia'),
(31, 'Dove'),
(10, 'Eisai Pharmaceuticals'),
(32, 'Fogg'),
(7, 'Getz Pharma'),
(1, 'GSK'),
(11, 'Hilton Pharma'),
(35, 'J.'),
(22, 'Johnson & Johnson'),
(33, 'Krone'),
(29, 'LifeCare'),
(18, 'Martin Dow'),
(26, 'Mediplus'),
(15, 'Merck'),
(23, 'Nestle'),
(34, 'Nivea'),
(5, 'Novartis'),
(4, 'Pfizer'),
(28, 'Pharmvo'),
(3, 'Reckitt Benckiser'),
(25, 'Roche'),
(6, 'Sami Pharma'),
(36, 'Sami Pharmaceuticals'),
(14, 'Sandoz'),
(12, 'Sanofi-Aventis'),
(9, 'Searle'),
(16, 'Servier'),
(20, 'Shaigan Pharmaceuticals'),
(19, 'Stiefel'),
(8, 'Wilson\'s Pharmaceuticals');

-- --------------------------------------------------------

--
-- Table structure for table `cart_items`
--

CREATE TABLE `cart_items` (
  `cart_item_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `variant_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL DEFAULT 1,
  `added_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `categories`
--

CREATE TABLE `categories` (
  `category_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `categories`
--

INSERT INTO `categories` (`category_id`, `name`) VALUES
(2, 'Antibiotics'),
(8, 'Baby Care'),
(4, 'Cold & Flu'),
(5, 'Diabetes Care'),
(6, 'Digestive Health'),
(10, 'Medical Devices'),
(9, 'Mental Health & Sedatives'),
(1, 'Pain Relief'),
(11, 'Personal Care'),
(7, 'Skin Care'),
(3, 'Vitamins & Supplements');

-- --------------------------------------------------------

--
-- Table structure for table `customers`
--

CREATE TABLE `customers` (
  `customer_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `address` varchar(255) DEFAULT NULL,
  `city` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `customers`
--

INSERT INTO `customers` (`customer_id`, `user_id`, `address`, `city`, `created_at`) VALUES
(1, 1, NULL, NULL, '2026-06-28 12:27:22'),
(2, 2, NULL, NULL, '2026-06-28 12:27:22'),
(3, 3, NULL, NULL, '2026-06-28 12:27:22'),
(4, 7, NULL, NULL, '2026-06-28 13:20:58'),
(5, 8, NULL, 'islamabad', '2026-06-30 12:03:23'),
(6, 9, NULL, NULL, '2026-07-02 20:40:32'),
(7, 10, NULL, 'islamabad', '2026-07-04 16:50:42'),
(8, 11, NULL, 'islamabad', '2026-07-05 11:20:52'),
(9, 12, NULL, NULL, '2026-07-05 17:01:57'),
(10, 13, 'FAWARA Chowk', 'Multan', '2026-07-07 06:02:20'),
(11, 16, 'AHMEDABAD', 'Multan', '2026-07-19 06:53:40'),
(12, 17, 'Gulshan road', 'Karachi', '2026-07-19 06:56:56'),
(13, 18, 'Janjua street 52', 'Faisalabad', '2026-07-24 15:38:36');

-- --------------------------------------------------------

--
-- Table structure for table `delivery_managers`
--

CREATE TABLE `delivery_managers` (
  `delivery_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `zone` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `delivery_managers`
--

INSERT INTO `delivery_managers` (`delivery_id`, `user_id`, `zone`) VALUES
(1, 6, 'Islamabad / Rawalpindi Zone'),
(2, 15, 'Islamabad - F Sectors');

-- --------------------------------------------------------

--
-- Table structure for table `medicines`
--

CREATE TABLE `medicines` (
  `medicine_id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL,
  `generic_name` varchar(150) DEFAULT NULL,
  `category_id` int(11) DEFAULT NULL,
  `brand_id` int(11) DEFAULT NULL,
  `type` enum('OTC','Prescription') NOT NULL DEFAULT 'OTC',
  `description` text DEFAULT NULL,
  `usage_info` text DEFAULT NULL,
  `side_effects` text DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `medicines`
--

INSERT INTO `medicines` (`medicine_id`, `name`, `generic_name`, `category_id`, `brand_id`, `type`, `description`, `usage_info`, `side_effects`, `image_url`, `is_active`) VALUES
(1, 'Panadol Tablet', 'Paracetamol 500mg', 1, 1, 'OTC', 'Paracetamol is a widely used analgesic and antipyretic that relieves mild to moderate pain and reduces fever. It works by blocking pain signals in the brain and helping the body release heat to lower temperature.', 'Adults: 1-2 tablets every 4-6 hours as needed. Do not exceed 8 tablets in 24 hours. Can be taken with or without food.', 'Generally well tolerated. Rare side effects include nausea, skin rash, or allergic reaction. Overdose can cause serious liver damage - never exceed recommended dose.', 'images/medicines/panadol-tablet.jpg', 1),
(2, 'Panadol Extra Tablet', 'Paracetamol 500mg + Caffeine 65mg', 1, 1, 'OTC', 'Panadol Extra combines paracetamol with caffeine, which enhances the pain-relieving effect for stronger relief from headaches and migraines.', 'Adults: 1-2 tablets every 4-6 hours as needed. Do not exceed 8 tablets in 24 hours.', 'May cause mild restlessness or difficulty sleeping due to caffeine content. Overdose can cause liver damage - never exceed recommended dose.', 'images/medicines/panadol-extra-tablet.jpg', 1),
(3, 'Calpol Tablet', 'Paracetamol 500mg', 1, 1, 'OTC', 'Calpol is a paracetamol-based analgesic and antipyretic used to relieve pain and reduce fever in adults.', 'Adults: 1-2 tablets every 4-6 hours as needed. Do not exceed 8 tablets in 24 hours.', 'Generally well tolerated. Rare side effects include nausea or allergic skin reaction. Avoid exceeding recommended dose.', 'images/medicines/calpol-tablet.jpg', 1),
(4, 'Brufen Tablet', 'Ibuprofen 200mg', 1, 2, 'OTC', 'Ibuprofen is a non-steroidal anti-inflammatory drug (NSAID) that reduces pain, inflammation, and fever. Commonly used for headaches, muscle pain, and menstrual cramps.', 'Adults: 1 tablet every 6-8 hours with food to reduce stomach upset. Do not exceed recommended daily dose unless directed by a doctor.', 'May cause stomach upset, heartburn, dizziness, or nausea. Long-term use can increase risk of stomach ulcers. Avoid in patients with kidney disease or active stomach ulcers.', 'images/medicines/brufen-tablet.jpg', 1),
(5, 'Disprin Tablet', 'Aspirin 300mg', 1, 3, 'OTC', 'Disprin is a fast-dissolving soluble aspirin tablet used for quick relief from headache, body pain, and fever. It also has a mild blood-thinning effect.', 'Dissolve 1-2 tablets in half a glass of water and drink. Adults only. Take after meals to reduce stomach irritation.', 'May cause stomach irritation, heartburn, or nausea. Not recommended for children under 16 years due to risk of Reye\'s syndrome. Avoid if you have a bleeding disorder.', 'images/medicines/disprin-tablet.jpg', 1),
(6, 'Ponstan Forte Capsule', 'Mefenamic Acid 500mg', 1, 4, 'OTC', 'Ponstan Forte is an NSAID capsule used for moderate to severe pain including menstrual cramps, headaches, toothaches, and muscle aches.', 'Take 1 capsule as directed by your doctor, usually with food to reduce stomach upset. Do not use for long-term pain without medical advice.', 'May cause stomach upset, drowsiness, or dizziness. Long-term use may increase risk of stomach bleeding. Avoid if allergic to NSAIDs.', 'images/medicines/ponstan-forte-capsule.jpg', 1),
(7, 'Ponstan Tablet', 'Mefenamic Acid 250mg', 1, 4, 'OTC', 'Ponstan is a lower-strength NSAID tablet used to relieve mild to moderate pain such as headaches, dental pain, and menstrual cramps.', 'Take 1 tablet with food, 2-3 times daily as directed by your doctor.', 'May cause stomach upset or drowsiness. Avoid prolonged use without medical supervision.', 'images/medicines/ponstan-tablet.jpg', 1),
(8, 'Voltral Tablet', 'Diclofenac Sodium 50mg', 1, 5, 'OTC', 'Voltral is an NSAID used to relieve pain and inflammation associated with arthritis, back pain, and musculoskeletal injuries.', 'Take 1 tablet 2-3 times daily with food, as directed by your doctor. Swallow whole - do not crush or chew.', 'May cause stomach upset, headache, or dizziness. Long-term use may increase risk of stomach bleeding and cardiovascular events.', 'images/medicines/voltral-tablet.jpg', 1),
(9, 'Voltral Emulgel', 'Diclofenac Diethylamine 1% (Topical)', 1, 5, 'OTC', 'Voltral Emulgel is a topical NSAID gel used for local relief of pain and inflammation in muscles and joints, such as sprains and back pain.', 'Apply a thin layer to the affected area 3-4 times daily and gently massage. Wash hands after application. For external use only.', 'May cause mild skin irritation, redness, or itching at the site of application. Avoid contact with eyes and open wounds.', 'images/medicines/voltral-emulgel.jpg', 1),
(10, 'Caflam Tablet', 'Diclofenac Potassium 50mg', 1, 5, 'OTC', 'Caflam is a fast-acting NSAID used for short-term relief of pain and inflammation, including post-operative and dental pain.', 'Take 1 tablet 2-3 times daily with food, as directed by your doctor.', 'May cause stomach upset, headache, or dizziness. Avoid long-term use without medical supervision.', 'images/medicines/caflam-tablet.jpg', 1),
(11, 'Methycobal Tablet', 'Mecobalamin (Methylcobalamin) 500mcg', 1, 11, 'OTC', 'Methycobal is a Vitamin B12 supplement (mecobalamin) used to support nerve health and relieve nerve-related pain such as tingling, numbness, and back pain caused by neuropathy.', 'Take 1 tablet daily, or as directed by your doctor. Best taken at the same time each day.', 'Generally well tolerated. Rare side effects include mild nausea or loss of appetite. Consult a doctor if symptoms persist.', 'images/medicines/methycobal-tablet.jpg', 1),
(12, 'Naprosyn Tablet', 'Naproxen 500mg', 1, 7, 'OTC', 'Naprosyn is an NSAID used to relieve pain, inflammation, and stiffness associated with arthritis and other musculoskeletal conditions.', 'Take 1 tablet twice daily with food, as directed by your doctor.', 'May cause stomach upset, heartburn, or dizziness. Long-term use may increase risk of stomach bleeding and cardiovascular events.', 'images/medicines/naprosyn-tablet.jpg', 1),
(13, 'Dicloran Tablet', 'Diclofenac Sodium 50mg', 1, 6, 'OTC', 'Dicloran is an NSAID used to relieve pain and inflammation from arthritis, muscle strains, and menstrual cramps.', 'Take 1 tablet 2-3 times daily with food, as directed by your doctor.', 'May cause stomach upset, headache, or dizziness. Avoid long-term use without medical supervision.', 'images/medicines/dicloran-tablet.jpg', 1),
(14, 'Dicloran SR Tablet', 'Diclofenac Sodium 100mg (Extended Release)', 1, 6, 'OTC', 'Dicloran SR is a sustained-release NSAID tablet providing longer-lasting relief from pain and inflammation, suitable for once or twice daily dosing.', 'Take 1 tablet daily with food, as directed by your doctor. Swallow whole - do not crush or chew.', 'May cause stomach upset, headache, or dizziness. Long-term use may increase risk of stomach bleeding.', 'images/medicines/dicloran-sr-tablet.jpg', 1),
(15, 'Starcox Tablet', 'Etoricoxib 60mg', 1, 7, 'OTC', 'Starcox is a selective COX-2 inhibitor NSAID used to relieve pain and inflammation in osteoarthritis and other joint conditions, with a lower risk of stomach irritation than traditional NSAIDs.', 'Take 1 tablet daily, with or without food, as directed by your doctor.', 'May cause indigestion, dizziness, or swelling. Use with caution in patients with heart or kidney conditions.', 'images/medicines/starcox-tablet.jpg', 1),
(16, 'Diagesic-P Tablet', 'Paracetamol 500mg + Thioridazine HCl 3mg + Caffeine 70mg', 1, 8, 'OTC', 'Diagesic-P is a combination analgesic used for mild to moderate pain such as headaches, muscle pain, and menstrual cramps, with added caffeine for enhanced pain relief.', 'Take 1-2 tablets every 4-6 hours as needed. Do not exceed 8 tablets in 24 hours.', 'May cause drowsiness due to its ingredients. Avoid driving or operating machinery until you know how it affects you.', 'images/medicines/diagesic-p-tablet.jpg', 1),
(17, 'Arinac Tablet', 'Ibuprofen 200mg + Pseudoephedrine 30mg', 1, 2, 'OTC', 'Arinac combines ibuprofen with a decongestant to relieve pain, fever, and nasal congestion associated with cold and sinus conditions.', 'Take 1 tablet every 6-8 hours with food, as needed. Do not exceed recommended daily dose.', 'May cause stomach upset, restlessness, or increased heart rate due to the decongestant. Avoid in patients with high blood pressure.', 'images/medicines/arinac-tablet.jpg', 1),
(18, 'Arinac Forte Tablet', 'Ibuprofen 400mg + Pseudoephedrine 60mg', 1, 2, 'OTC', 'Arinac Forte is a stronger combination of ibuprofen and decongestant, used for pain, fever, and nasal congestion relief in cold and flu.', 'Take 1 tablet every 6-8 hours with food, as needed. Do not exceed recommended daily dose.', 'May cause stomach upset, restlessness, or increased heart rate due to the decongestant. Avoid in patients with high blood pressure.', 'images/medicines/arinac-forte-tablet.jpg', 1),
(19, 'Nuberol Forte Tablet', 'Paracetamol 650mg + Orphenadrine 50mg', 1, 9, 'OTC', 'Nuberol Forte combines paracetamol with a muscle relaxant to relieve pain and stiffness from muscle spasms, back pain, and musculoskeletal injuries.', 'Take 1 tablet 2-3 times daily as directed by your doctor. Swallow whole with water.', 'May cause drowsiness, dry mouth, or dizziness. Avoid driving or operating machinery until you know how it affects you.', 'images/medicines/nuberol-forte-tablet.jpg', 1),
(20, 'Nuberol Tablet', 'Paracetamol 450mg + Orphenadrine 35mg', 1, 9, 'OTC', 'Nuberol is a milder combination of paracetamol and a muscle relaxant, used for relief from muscle pain, spasms, and stiffness.', 'Take 1 tablet 2-3 times daily as directed by your doctor.', 'May cause mild drowsiness or dry mouth. Avoid driving or operating machinery until you know how it affects you.', 'images/medicines/nuberol-tablet.jpg', 1),
(21, 'Augmentin Tablet', 'Amoxicillin 500mg + Clavulanic Acid 125mg', 2, 1, 'OTC', 'Augmentin is a broad-spectrum antibiotic combining amoxicillin with clavulanic acid, used to treat a wide range of bacterial infections including respiratory, ear, and urinary tract infections.', 'Take as prescribed by your doctor, usually every 8-12 hours with food to reduce stomach upset. Complete the full course even if you feel better.', 'May cause nausea, diarrhea, or stomach upset. Rare allergic reactions can occur - seek medical help if rash or difficulty breathing develops.', 'images/medicines/augmentin-tablet.jpg', 1),
(22, 'Amoxil Capsule', 'Amoxicillin 500mg', 2, 1, 'OTC', 'Amoxil is a penicillin-type antibiotic used to treat bacterial infections of the ear, nose, throat, urinary tract, and skin.', 'Take as prescribed, usually every 8 hours. Complete the full course of treatment even if symptoms improve early.', 'May cause nausea, diarrhea, or skin rash. Inform your doctor if you are allergic to penicillin.', 'images/medicines/amoxil-capsule.jpg', 1),
(23, 'Klaricid Tablet', 'Clarithromycin 500mg', 2, 2, 'OTC', 'Klaricid is a macrolide antibiotic used to treat respiratory tract infections, skin infections, and H. pylori-related stomach ulcers.', 'Take 1 tablet twice daily as directed by your doctor, with or without food.', 'May cause stomach upset, altered taste, or headache. Inform your doctor of any other medications you are taking.', 'images/medicines/klaricid-tablet.jpg', 1),
(24, 'Azomax Tablet', 'Azithromycin 500mg', 2, 5, 'OTC', 'Azomax is a macrolide antibiotic effective against a wide variety of bacterial infections, often prescribed as a short 3-5 day course.', 'Take once daily as directed by your doctor, typically for 3 days. Take on an empty stomach for best absorption.', 'May cause stomach upset, diarrhea, or nausea. Complete the full course even if symptoms resolve early.', 'images/medicines/azomax-tablet.jpg', 1),
(25, 'Velosef Capsule', 'Cephradine 500mg', 2, 1, 'OTC', 'Velosef is a cephalosporin antibiotic used to treat respiratory, urinary tract, skin, and ear infections.', 'Take as prescribed, usually every 6 hours. Complete the full course of treatment.', 'May cause stomach upset, diarrhea, or allergic skin reactions.', 'images/medicines/velosef-capsule.jpg', 1),
(26, 'Novidat Tablet', 'Ciprofloxacin 500mg', 2, 6, 'OTC', 'Novidat is a fluoroquinolone antibiotic used to treat urinary tract, gastrointestinal, and respiratory infections.', 'Take twice daily as directed by your doctor. Avoid taking with dairy products or antacids, which reduce absorption.', 'May cause nausea, dizziness, or tendon pain. Avoid excessive sun exposure while taking this medicine.', 'images/medicines/novidat-tablet.jpg', 1),
(27, 'Cefspan Capsule', 'Cefixime 400mg', 2, 13, 'OTC', 'Cefspan is a broad-spectrum cephalosporin antibiotic used for urinary tract infections, ear infections, and respiratory infections, with the convenience of once-daily dosing.', 'Take once daily as directed by your doctor, with or without food.', 'May cause stomach upset, diarrhea, or headache. Not for viral infections such as cold or flu.', 'images/medicines/cefspan-capsule.jpg', 1),
(28, 'Erythrocin Tablet', 'Erythromycin 250mg', 2, 2, 'OTC', 'Erythrocin is a macrolide antibiotic used for respiratory, skin, and soft tissue infections, especially for patients allergic to penicillin.', 'Take every 6 hours as directed by your doctor, preferably on an empty stomach.', 'May cause stomach upset, nausea, or abdominal cramps.', 'images/medicines/erythrocin-tablet.jpg', 1),
(29, 'Ospamox Capsule', 'Amoxicillin 500mg', 2, 14, 'OTC', 'Ospamox is a penicillin-type antibiotic used to treat a variety of bacterial infections including respiratory and urinary tract infections.', 'Take as prescribed by your doctor, usually every 8 hours. Complete the full course.', 'May cause nausea, diarrhea, or allergic skin reactions.', 'images/medicines/ospamox-capsule.jpg', 1),
(30, 'Amaryl Tablet', 'Glimepiride 2mg', 5, 12, 'OTC', 'Amaryl is a sulfonylurea medicine that helps the pancreas release more insulin, used to control blood sugar in type 2 diabetes.', 'Take once daily with breakfast or the first main meal, as directed by your doctor.', 'May cause low blood sugar (hypoglycemia), weight gain, or stomach upset. Monitor blood sugar regularly.', 'images/medicines/amaryl-tablet.jpg', 1),
(31, 'Glucophage Tablet', 'Metformin 500mg', 5, 15, 'OTC', 'Glucophage is the most commonly prescribed first-line medicine for type 2 diabetes, helping to lower blood sugar by improving insulin sensitivity.', 'Take with meals as directed by your doctor to reduce stomach upset. Do not crush or chew extended-release forms.', 'May cause nausea, diarrhea, or stomach upset, especially when starting. Long-term use may lower vitamin B12 levels.', 'images/medicines/glucophage-tablet.jpg', 1),
(32, 'Januvia Tablet', 'Sitagliptin 100mg', 5, 15, 'OTC', 'Januvia is a DPP-4 inhibitor that helps control blood sugar in type 2 diabetes by increasing insulin release after meals.', 'Take once daily, with or without food, as directed by your doctor.', 'May cause headache, upper respiratory infection symptoms, or joint pain. Rarely, pancreatitis - seek help for severe abdominal pain.', 'images/medicines/januvia-tablet.jpg', 1),
(33, 'Galvus Tablet', 'Vildagliptin 50mg', 5, 5, 'OTC', 'Galvus is a DPP-4 inhibitor used alongside diet and exercise to control blood sugar in type 2 diabetes.', 'Take twice daily, morning and evening, as directed by your doctor.', 'May cause dizziness, tremor, or headache. Liver function may be monitored periodically.', 'images/medicines/galvus-tablet.jpg', 1),
(34, 'Glucobay Tablet', 'Acarbose 50mg', 5, 17, 'OTC', 'Glucobay slows the digestion of carbohydrates, helping to reduce blood sugar spikes after meals in type 2 diabetes.', 'Take with the first bite of each main meal, as directed by your doctor.', 'May cause bloating, gas, or diarrhea, especially when starting treatment.', 'images/medicines/glucobay-tablet.jpg', 1),
(35, 'Getformin Tablet', 'Glimepiride 2mg + Metformin HCl 500mg', 5, 7, 'OTC', 'Getformin combines two diabetes medicines in one tablet, helping the body produce more insulin while also improving insulin sensitivity.', 'Take as directed by your doctor, usually with meals.', 'May cause low blood sugar, nausea, or stomach upset. Monitor blood sugar regularly.', 'images/medicines/getformin-tablet.jpg', 1),
(36, 'Daonil Tablet', 'Glibenclamide 5mg', 5, 12, 'OTC', 'Daonil is a sulfonylurea used to control blood sugar in type 2 diabetes by stimulating insulin release from the pancreas.', 'Take once daily with breakfast, as directed by your doctor.', 'May cause low blood sugar, weight gain, or nausea. Do not skip meals after taking this medicine.', 'images/medicines/daonil-tablet.jpg', 1),
(37, 'Diamicron MR Tablet', 'Gliclazide 30mg', 5, 16, 'OTC', 'Diamicron MR is a modified-release sulfonylurea that helps control blood sugar throughout the day in type 2 diabetes.', 'Take once daily with breakfast, swallow whole - do not crush or chew.', 'May cause low blood sugar, headache, or stomach upset.', 'images/medicines/diamicron-mr-tablet.jpg', 1),
(38, 'Neurobion Tablet', 'Vitamin B1 + B6 + B12', 3, 15, 'OTC', 'Neurobion is a B-vitamin supplement that supports healthy nerve function and helps relieve nerve-related pain and tingling.', 'Take 1 tablet daily, or as directed by your doctor.', 'Generally well tolerated. Rare side effects include mild nausea.', 'images/medicines/neurobion-tablet.jpg', 1),
(39, 'Sangobion Capsule', 'Iron + Folic Acid + Multivitamin', 3, 18, 'OTC', 'Sangobion is an iron supplement combined with vitamins, used to prevent and treat iron-deficiency anemia and support overall vitality.', 'Take 1 capsule daily, or as directed by your doctor, preferably after meals.', 'May cause mild stomach upset or constipation. Stools may appear darker - this is normal.', 'images/medicines/sangobion-capsule.jpg', 1),
(40, 'CAC-1000 Plus Tablet', 'Calcium Carbonate + Vitamin D3', 3, 5, 'OTC', 'CAC-1000 Plus supports bone health by providing calcium along with vitamin D3 for better absorption.', 'Take 1 tablet daily, or as directed by your doctor.', 'May cause mild stomach upset or constipation in some people.', 'images/medicines/cac-1000-plus-tablet.jpg', 1),
(41, 'Evion Capsule', 'Vitamin E 400mg', 3, 15, 'OTC', 'Evion is a Vitamin E supplement that acts as an antioxidant, supporting skin health and overall cellular protection.', 'Take 1 capsule daily, or as directed by your doctor.', 'Generally well tolerated at recommended doses.', 'images/medicines/evion-capsule.jpg', 1),
(42, 'Centrum Tablet', 'Multivitamin + Multimineral', 3, 1, 'OTC', 'Centrum is a complete daily multivitamin providing a broad range of essential vitamins and minerals to support overall health.', 'Take 1 tablet daily with food.', 'Generally well tolerated. Take with food to reduce mild stomach upset.', 'images/medicines/centrum-tablet.jpg', 1),
(43, 'Polybion Tablet', 'Vitamin B Complex', 3, 15, 'OTC', 'Polybion is a B-complex vitamin supplement that supports energy metabolism and healthy nerve and skin function.', 'Take 1 tablet daily, or as directed by your doctor.', 'Generally well tolerated. Rare side effects include mild nausea.', 'images/medicines/polybion-tablet.jpg', 1),
(44, 'Iberet Folic Tablet', 'Iron + Folic Acid + Vitamin C + B-Complex', 3, 2, 'OTC', 'Iberet Folic is a controlled-release iron and multivitamin supplement, commonly used to treat and prevent iron-deficiency anemia, including during pregnancy.', 'Take 1 tablet daily, or as directed by your doctor, preferably after meals.', 'May cause mild stomach upset or constipation. Stools may appear darker - this is normal.', 'images/medicines/iberet-folic-tablet.jpg', 1),
(45, 'Surbex-Z Tablet', 'Multivitamin + Zinc', 3, 2, 'OTC', 'Surbex-Z combines B-complex vitamins with zinc to support energy levels, immunity, and healthy skin.', 'Take 1 tablet daily, or as directed by your doctor.', 'Generally well tolerated. Rare side effects include mild nausea.', 'images/medicines/surbex-z-tablet.jpg', 1),
(46, 'Actifed-P Cold Tablet', 'Triprolidine HCl + Pseudoephedrine HCl + Paracetamol', 4, 1, 'OTC', 'Actifed-P Cold relieves multiple cold and flu symptoms at once, including runny nose, congestion, fever, and body aches.', 'Take 1 tablet every 6-8 hours as needed. Do not exceed 4 tablets in 24 hours.', 'May cause drowsiness. Avoid driving or operating machinery until you know how it affects you.', 'images/medicines/actifed-p-cold-tablet.jpg', 1),
(47, 'Arinac Suspension', 'Ibuprofen 100mg + Pseudoephedrine HCl 15mg (per 5ml)', 4, 2, 'OTC', 'Arinac Suspension relieves cold, fever, and flu symptoms in a liquid form, combining a pain/fever reducer with a decongestant.', 'Take as directed on the label or by your doctor, based on age and weight. Shake well before use.', 'May cause stomach upset or restlessness due to the decongestant. Avoid in patients with high blood pressure.', 'images/medicines/arinac-suspension.jpg', 1),
(48, 'Panadol Cold & Flu Tablet', 'Paracetamol + Phenylephrine + Caffeine', 4, 1, 'OTC', 'Panadol Cold & Flu relieves the symptoms of cold and flu including headache, fever, body aches, and nasal congestion.', 'Take 1-2 tablets every 4-6 hours as needed. Do not exceed 8 tablets in 24 hours.', 'May cause mild restlessness due to caffeine and phenylephrine content.', 'images/medicines/panadol-cold-flu-tablet.jpg', 1),
(49, 'Coldene Tablet', 'Pheniramine Maleate + Pseudoephedrine + Mepyramine Maleate + Paracetamol', 4, 8, 'OTC', 'Coldene relieves multiple cold, fever, and flu symptoms including runny nose, sneezing, watery eyes, and body aches.', 'Adults: take 1 tablet 2-4 times daily as needed. Not recommended for children 12 or younger.', 'May cause drowsiness due to antihistamine content. Avoid driving or operating machinery.', 'images/medicines/coldene-tablet.jpg', 1),
(50, 'Buscopan Tablet', 'Hyoscine Butylbromide 10mg', 6, 12, 'OTC', 'Buscopan relieves stomach cramps and abdominal pain caused by spasms of the digestive tract.', 'Take 1-2 tablets up to 3 times daily as needed, or as directed by your doctor.', 'Generally well tolerated. May cause dry mouth or mild dizziness.', 'images/medicines/buscopan-tablet.jpg', 1),
(51, 'Eno Sachet', 'Sodium Bicarbonate + Citric Acid (Antacid)', 6, 1, 'OTC', 'Eno is a fast-acting effervescent antacid that provides quick relief from acidity, indigestion, and heartburn.', 'Dissolve 1 sachet in a glass of water and drink. Can be taken after meals or when symptoms occur.', 'Generally safe. Avoid excessive use due to sodium content, especially in patients with high blood pressure.', 'images/medicines/eno-sachet.jpg', 1),
(52, 'Enterogermina Suspension', 'Bacillus Clausii Spores (Probiotic)', 6, 12, 'OTC', 'Enterogermina is a probiotic supplement that helps restore healthy gut bacteria, commonly used for diarrhea and after antibiotic use.', 'Take 1 vial 2-3 times daily, or as directed by your doctor. Shake well before use.', 'Generally very well tolerated with minimal side effects.', 'images/medicines/enterogermina-suspension.jpg', 1),
(53, 'Nexum Tablet', 'Esomeprazole 40mg', 6, 7, 'OTC', 'Nexum reduces stomach acid production, used to treat acid reflux, heartburn, and stomach ulcers.', 'Take 1 tablet daily before a meal, as directed by your doctor. Swallow whole - do not crush or chew.', 'May cause headache, stomach upset, or diarrhea with long-term use.', 'images/medicines/nexum-tablet.jpg', 1),
(54, 'Motilium Tablet', 'Domperidone 10mg', 6, 22, 'OTC', 'Motilium relieves nausea, vomiting, and bloating by helping the stomach empty more quickly.', 'Take 1 tablet 3 times daily before meals, as directed by your doctor.', 'May rarely cause dry mouth or headache. Consult a doctor before use if you have heart conditions.', 'images/medicines/motilium-tablet.jpg', 1),
(55, 'No-Spa Tablet', 'Drotaverine HCl 40mg', 6, 12, 'OTC', 'No-Spa relieves smooth muscle spasms, commonly used for stomach cramps, menstrual cramps, and digestive discomfort.', 'Take 1-2 tablets up to 3 times daily as needed, or as directed by your doctor.', 'Generally well tolerated. May cause mild dizziness or palpitations.', 'images/medicines/no-spa-tablet.jpg', 1),
(56, 'Risek Capsule', 'Omeprazole 20mg', 6, 7, 'OTC', 'Risek reduces stomach acid production, used to treat acid reflux, heartburn, and stomach ulcers.', 'Take 1 capsule daily before a meal, as directed by your doctor. Swallow whole - do not crush or chew.', 'May cause headache, stomach upset, or diarrhea with long-term use.', 'images/medicines/risek-capsule.jpg', 1),
(57, 'Spasler Neo Tablet', 'Mebeverine HCl 135mg', 6, 24, 'OTC', 'Spasler Neo relieves abdominal cramps and pain associated with irritable bowel syndrome (IBS) and digestive spasms.', 'Take 1 tablet 3 times daily, 20 minutes before meals, as directed by your doctor.', 'Generally well tolerated. Rare side effects include mild allergic skin reactions.', 'images/medicines/spasler-neo-tablet.jpg', 1),
(58, 'Clobevate Cream', 'Clobetasol Propionate 0.05%', 7, 19, 'OTC', 'Clobevate is a potent topical corticosteroid used to relieve inflammation, itching, and redness in various skin conditions such as eczema and psoriasis.', 'Apply a thin layer to the affected area once or twice daily, as directed by your doctor. Avoid prolonged use.', 'May cause skin thinning, burning, or irritation with prolonged use. For external use only.', 'images/medicines/clobevate-cream.jpg', 1),
(59, 'Dermovate Cream', 'Clobetasol Propionate', 7, 1, 'OTC', 'Dermovate is a potent topical corticosteroid used for short-term treatment of severe skin inflammation, eczema, and psoriasis.', 'Apply a thin layer to the affected area once or twice daily, as directed by your doctor. Avoid prolonged use.', 'May cause skin thinning, burning, or irritation with prolonged use. For external use only.', 'images/medicines/dermovate-cream.jpg', 1),
(60, 'Fudic Cream', 'Fusidic Acid 2%', 7, 20, 'OTC', 'Fudic is a topical antibiotic cream used to treat bacterial skin infections such as impetigo and infected wounds.', 'Apply a thin layer to the affected area 3-4 times daily, as directed by your doctor.', 'May cause mild skin irritation or itching at the site of application. For external use only.', 'images/medicines/fudic-cream.jpg', 1),
(61, 'Healit Skin Ointment', 'Bacitracin + Polymyxin + Neomycin + Lidocaine', 7, 21, 'OTC', 'Healit is a triple-antibiotic ointment with a local anesthetic, used to prevent infection and relieve pain in minor cuts, burns, and wounds.', 'Apply a small amount to the affected area 1-3 times daily, or as directed by your doctor.', 'May rarely cause allergic skin reactions. For external use only - avoid contact with eyes.', 'images/medicines/healit-ointment.jpg', 1),
(62, 'Betnovate-N Cream', 'Betamethasone + Neomycin', 7, 1, 'OTC', 'Betnovate-N combines a corticosteroid with an antibiotic to treat inflamed skin conditions that are also infected or at risk of infection.', 'Apply a thin layer to the affected area 2-3 times daily, as directed by your doctor.', 'May cause skin thinning or irritation with prolonged use. For external use only.', 'images/medicines/betnovate-n-cream.jpg', 1),
(63, 'Polyfax Skin Ointment', 'Polymyxin B + Bacitracin Zinc', 7, 1, 'OTC', 'Polyfax is an antibiotic ointment used to prevent and treat minor bacterial skin infections such as cuts, scrapes, and burns.', 'Apply a small amount to the affected area 1-3 times daily.', 'May rarely cause mild skin irritation. For external use only - avoid contact with eyes.', 'images/medicines/polyfax-ointment.jpg', 1),
(64, 'Johnson\'s Baby Powder', 'Baby Skincare (Talc-based)', 8, 22, 'OTC', 'Johnson\'s Baby Powder gently absorbs moisture and helps keep baby\'s skin soft, dry, and comfortable.', 'Sprinkle a small amount onto clean, dry skin after bathing. Avoid direct application near the face.', 'For external use only. Keep away from baby\'s face to avoid inhalation.', 'images/medicines/johnsons-baby-powder.jpg', 1),
(65, 'Johnson\'s Baby Lotion', 'Baby Skincare (Moisturizer)', 8, 22, 'OTC', 'Johnson\'s Baby Lotion gently moisturizes and nourishes baby\'s delicate skin, keeping it soft and smooth.', 'Apply gently to baby\'s skin after bath time or as needed throughout the day.', 'For external use only. Generally very gentle and well tolerated.', 'images/medicines/johnsons-baby-lotion.jpg', 1),
(66, 'Cerelac Rice Cereal', 'Infant Cereal (6 Months+)', 8, 23, 'OTC', 'Cerelac Rice Cereal is a nutrient-fortified first weaning food for babies starting solids, enriched with protein, calcium, vitamin B1, and iron.', 'Mix with warm water or milk to the desired consistency, as per the instructions on the pack. Suitable for babies from 6 months.', 'Introduce gradually and watch for any food allergies. Consult a pediatrician before starting solids.', 'images/medicines/cerelac-rice-cereal.jpg', 1),
(67, 'Cerelac Red Fruits Cereal', 'Infant Cereal (1 Year+)', 8, 23, 'OTC', 'Cerelac Red Fruits Cereal is a fruit-flavored, nutrient-fortified cereal for toddlers, providing essential vitamins and iron with a taste kids enjoy.', 'Mix with warm water or milk to the desired consistency, as per the instructions on the pack. Suitable for children from 1 year.', 'Introduce gradually and watch for any food allergies.', 'images/medicines/cerelac-red-fruits-cereal.jpg', 1),
(68, 'Lactogen 1 Infant Formula', 'Infant Formula Milk (0-6 Months)', 8, 23, 'OTC', 'Lactogen 1 is an infant formula designed to support healthy growth and development in babies from birth to 6 months, for when breastfeeding is not possible.', 'Prepare according to the instructions on the pack using boiled, cooled water. Follow feeding guidelines by age/weight.', 'Breastfeeding is recommended as the best source of nutrition for infants. Use formula under medical guidance.', 'images/medicines/lactogen-1-formula.jpg', 1),
(69, 'Panadol Baby Drops', 'Paracetamol (Pediatric)', 8, 1, 'OTC', 'Panadol Baby Drops relieve fever and mild pain in infants and young children, such as discomfort from teething or vaccinations.', 'Give the age/weight-appropriate dose using the dropper provided. Do not exceed the recommended dose - consult a doctor for infants under 3 months.', 'Generally well tolerated at recommended doses. Never exceed the maximum daily dose.', 'images/medicines/panadol-baby-drops.jpg', 1),
(70, 'Alp Tablet 0.25mg', 'Alprazolam 0.25mg', 9, 11, 'Prescription', 'Alp is a benzodiazepine used for the short-term treatment of anxiety disorders and panic attacks. It works by calming excessive activity in the brain.', 'Take exactly as prescribed by your doctor. Do not increase the dose or use for longer than prescribed - this medicine can be habit-forming.', 'May cause drowsiness, dizziness, or dependence with prolonged use. Do not combine with alcohol. Avoid driving or operating machinery until you know how it affects you.', 'images/medicines/alp-tablet-0.25mg.jpg', 1),
(71, 'Alp Tablet 0.5mg', 'Alprazolam 0.5mg', 9, 11, 'Prescription', 'Alp is a benzodiazepine used for the short-term treatment of anxiety disorders and panic attacks. It works by calming excessive activity in the brain.', 'Take exactly as prescribed by your doctor. Do not increase the dose or use for longer than prescribed - this medicine can be habit-forming.', 'May cause drowsiness, dizziness, or dependence with prolonged use. Do not combine with alcohol. Avoid driving or operating machinery until you know how it affects you.', 'images/medicines/alp-tablet-0.5mg.jpg', 1),
(72, 'Accu-Chek Instant S', NULL, 10, 25, 'OTC', 'Blood Glucose Meter and Lancing Device. M.R.P. Rs 3,349.00', NULL, NULL, 'images/medicines/accu_chek_instant_s.png', 1),
(73, 'Mediplus Premium Quality Mini Nebulizer', NULL, 10, 26, 'OTC', 'Premium Quality Mini Nebulizer MN-9025', NULL, NULL, 'images/medicines/mediplus_nebulizer.png', 1),
(74, 'believia Wrist-type Digital Blood Pressure Monitor', NULL, 10, 27, 'OTC', 'Wrist-type Digital Blood Pressure Monitor BP 30W', NULL, NULL, 'images/medicines/believia_bp_monitor.png', 1),
(75, 'Pharmvo EvoCheck GO', NULL, 10, 28, 'OTC', 'Blood Glucose Monitoring System', NULL, NULL, 'images/medicines/evocheck_go.png', 1),
(76, 'LifeCare Medical Nebulizer', NULL, 10, 29, 'OTC', 'Nebulizer Compressor System LC-605', NULL, NULL, 'images/medicines/lifecare_nebulizer.png', 1),
(77, 'Adidas Ice Dive Deo Body Spray', 'Deodorant Body Spray', 11, 30, 'OTC', 'Adidas Ice Dive Deo Body Spray delivers 24-hour fresh power with an invigorating aquatic fragrance. Developed with athletes for long-lasting confidence and freshness throughout your active day.', 'Hold 15cm from skin and spray on chest and underarms. Avoid contact with eyes and broken skin. For external use only.', 'May cause irritation on sensitive skin. Discontinue use if rash or redness occurs. Keep away from flames.', 'images/medicines/Adidas_Ice_Dive_Body.png', 1),
(78, 'Dove Go Fresh Cucumber & Green Tea Spray', 'Antiperspirant Deodorant Spray', 11, 31, 'OTC', 'Dove Go Fresh Cucumber & Green Tea Antiperspirant provides 48-hour protection against sweat and odour with ¼ moisturising cream. Its refreshing cucumber and green tea scent keeps you feeling beautifully fresh all day.', 'Shake well before use. Hold 15cm away from underarms and spray evenly. Allow to dry before dressing. Reapply as needed.', 'Avoid use on irritated or broken skin. If irritation develops, discontinue use. Contains aluminium salts.', 'images/medicines/Dove_Go_Fresh_Cucumber_And_Green_Tea.png', 1),
(79, 'Fogg Arabia Intense Oud Body Spray', 'Perfume Body Spray', 11, 32, 'OTC', 'Fogg Arabia Intense Oud is a premium no-gas body spray with rich Arabian oud fragrance. Its concentrated perfume formula delivers up to 800 sprays per bottle, making every spray count with a long-lasting, luxurious scent.', 'Spray directly on pulse points — wrists, neck, and behind ears. No gas formula ensures consistent output till last drop. For external use only.', 'Avoid spraying on face or near eyes. May stain light-coloured fabrics. If skin irritation occurs, discontinue use.', 'images/medicines/Fogg_Arabia_Intense_Oud_Body.png', 1),
(80, 'Krone Dune Noir Body Spray', 'Body Spray', 11, 33, 'OTC', 'Krone Dune Noir is a bold and mysterious fragrance that opens with fresh citrus top notes, transitioning into a warm woody base with hints of musk. Perfect for the modern man who commands attention.', 'Shake well and spray 15-20cm away from body. Apply on chest, neck and pulse points for best results. For external use only.', 'Avoid use on broken or irritated skin. Keep away from eyes and mucous membranes. Flammable — do not spray near open flames.', 'images/medicines/Krone_Dune_Noir_Body_Spray.png', 1),
(81, 'Nivea Dry Comfort Deodorant Spray', 'Antiperspirant Deodorant', 11, 34, 'OTC', 'Nivea Dry Comfort provides reliable 48-hour protection against sweat and body odour. Its Dual Active formula combines powerful antiperspirant protection with gentle skin care for dry, comfortable underarms all day long.', 'Shake can before use. Spray onto clean, dry underarms from approximately 15cm distance. Allow to dry before dressing.', 'Do not apply on irritated, damaged or freshly shaved skin. Avoid inhalation. Contains aluminium chlorohydrate.', 'images/medicines/Nivea_Dry_Comfort_Deodorant_Spray.png', 1),
(82, 'J. Burn Perfume Body Spray', 'Perfume Body Spray', 11, 35, 'OTC', 'J. Burn Pour Homme is a fiery, passionate fragrance crafted for the confident man. Its bold red packaging reflects the intense spicy-woody notes within — a head-turning scent that lingers from morning to night.', 'Spray generously on chest, neck and wrists. Reapply as desired for lasting fragrance. For external use only. Keep cap on when not in use.', 'For external use only. Avoid contact with eyes. If rash or irritation occurs, discontinue use. Keep away from heat and flames.', 'images/medicines/burn_1.jpg', 1),
(83, 'J. Endeavor Perfume Body Spray', 'Perfume Body Spray', 11, 35, 'OTC', 'J. Endeavor is a premium no-gas perfume body spray for men, delivering a sophisticated dark-toned fragrance with deep woody and musk notes. Its sleek black bottle reflects the bold, modern man it\'s designed for.', 'Apply on pulse points for maximum effect. The no-gas formula delivers pure perfume. Shake gently before spraying. For external use only.', 'Avoid contact with eyes and broken skin. Discontinue if irritation occurs. Keep away from children. Store in a cool, dry place.', 'images/medicines/endeavor.jpg', 1),
(84, 'J. Enigma Perfume Body Spray', 'Perfume Body Spray', 11, 35, 'OTC', 'J. Enigma is a captivating no-gas perfume body spray with vibrant citrus top notes and an enigmatic aromatic base. Its striking yellow and black design mirrors the electric energy of its unforgettable scent.', 'Spray on neck, chest and wrists. The no-gas formula ensures a fine mist of pure fragrance. For external use only.', 'Avoid spraying on face or near eyes. May cause irritation on very sensitive skin. Keep away from open flames and heat sources.', 'images/medicines/enigma.jpg', 1),
(85, 'J. Exodus Perfume Body Spray', 'Perfume Body Spray', 11, 35, 'OTC', 'J. Exodus is a refreshing no-gas perfume body spray featuring cool aquatic and green notes. Its bold green and black packaging embodies the spirit of adventure and freshness that defines the modern gentleman.', 'Shake gently and spray on pulse points — wrists, neck, behind ears. No-gas formula for pure fragrance delivery. For external use only.', 'For external use only. Avoid contact with eyes. Discontinue if skin irritation occurs. Do not ingest.', 'images/medicines/exodus.jpg', 1),
(86, 'J. Velocity Perfume Body Spray', 'Perfume Body Spray', 11, 35, 'OTC', 'J. Velocity is an energising no-gas perfume body spray with dynamic citrus and warm amber notes. Its vivid orange and black design captures the speed and intensity of a man on the move.', 'Apply on pulse points for long-lasting fragrance. Shake gently before use. The no-gas formula ensures pure perfume in every spray. For external use only.', 'Avoid contact with eyes and mucous membranes. Discontinue if rash or redness develops. Keep away from children and heat sources.', 'images/medicines/velocity.jpg', 1),
(87, 'J. La Seduction Rejuvenating Anti-Ageing Serum', 'Anti-Ageing Face Serum', 11, 35, 'OTC', 'J. La Seduction is a luxurious rejuvenating anti-ageing serum formulated with paraben-free, dermatologically tested ingredients. Its non-greasy formula absorbs quickly to reduce fine lines, improve skin elasticity, and deliver a youthful, radiant glow.', 'Apply 2-3 drops on clean face and neck. Gently massage in upward circular motions until absorbed. Use morning and evening for best results. Follow with moisturiser and sunscreen (AM).', 'Patch test recommended before first use. Avoid contact with eyes. If irritation occurs, reduce frequency of application or discontinue.', 'images/medicines/la_esduction.jpg', 1),
(88, 'J. Soothing Twilight Hand Cream', 'Moisturising Hand Cream', 11, 35, 'OTC', 'J. Soothing Twilight Hand Cream is a richly moisturising formula that nourishes and protects dry, tired hands. Infused with calming twilight-inspired fragrance, it leaves skin silky soft and delicately scented without any greasy residue.', 'Squeeze a small amount onto hands and massage gently until absorbed. Reapply throughout the day as needed, especially after washing hands.', 'For external use only. Avoid contact with eyes. If irritation occurs, discontinue use. Keep out of reach of children.', 'images/medicines/la_generation_1.jpg', 1),
(89, 'Tramal 50mg Capsules', 'Tramadol HCl 50mg', 9, 9, 'Prescription', 'Tramal 50mg Capsules contain Tramadol HCl, a centrally-acting opioid analgesic used for the relief of moderate to moderately severe pain. It works by binding to opioid receptors in the brain and inhibiting the reuptake of serotonin and norepinephrine, providing dual-mechanism pain relief. Manufactured by Searle Pakistan.\n\n⚡ ADVANTAGES:\n• Effective for moderate to severe pain (post-surgical, dental, musculoskeletal)\n• Dual mechanism — opioid + serotonin/norepinephrine reuptake inhibition\n• Lower abuse potential compared to stronger opioids like morphine\n• Fast onset of action (within 30-60 minutes)\n• Available in convenient capsule form\n\n⚠️ DISADVANTAGES:\n• Risk of dependence and tolerance with prolonged use\n• Can cause nausea, dizziness, drowsiness, and constipation\n• Not suitable for patients with seizure disorders\n• Dangerous if combined with alcohol, sedatives, or antidepressants\n• Prescription-only — requires doctor supervision', 'Take 1-2 capsules every 4-6 hours as needed for pain, or as directed by your physician. Swallow whole with water — do not crush or chew. Maximum daily dose: 400mg (8 capsules). Start with the lowest effective dose. Do not exceed prescribed duration. Not recommended for children under 12 years.', 'Common: Nausea, dizziness, drowsiness, headache, constipation, dry mouth. Less common: Sweating, vomiting, itching, fatigue. Serious (seek immediate help): Seizures, difficulty breathing, severe allergic reaction, serotonin syndrome (agitation, hallucinations, rapid heartbeat, fever). Risk of dependence with long-term use. Do not stop abruptly — taper under medical guidance.', 'images/medicines/Tramal_50mg_Capsules_10s.png', 1),
(90, 'Tramal Plus Tablets', 'Tramadol HCl 37.5mg + Paracetamol 325mg', 9, 9, 'Prescription', 'Tramal Plus combines Tramadol HCl (37.5mg) with Paracetamol (325mg) for enhanced pain relief through a synergistic dual-analgesic approach. The combination allows lower doses of each component while maintaining strong efficacy for acute and chronic pain management. Manufactured by Searle Pakistan.\n\n⚡ ADVANTAGES:\n• Synergistic combination provides better pain relief than either drug alone\n• Lower tramadol dose (37.5mg) reduces opioid-related side effects\n• Effective for dental pain, post-operative pain, and musculoskeletal pain\n• Paracetamol adds antipyretic (fever-reducing) benefit\n• Well-studied combination with proven clinical efficacy\n\n⚠️ DISADVANTAGES:\n• Still carries opioid dependence risk (though lower than Tramal 50mg alone)\n• Paracetamol component limits maximum daily dose to avoid liver toxicity\n• Not suitable for patients with liver disease or chronic alcohol use\n• Drowsiness may impair driving and operating machinery\n• Requires prescription and medical supervision', 'Take 1-2 tablets every 4-6 hours as needed, or as directed by physician. Maximum: 8 tablets per day. Do not exceed 4g of paracetamol daily from all sources combined. Swallow whole with water. Avoid alcohol. Not for children under 12.', 'Common: Nausea, drowsiness, dizziness, constipation, sweating. Less common: Headache, vomiting, dry mouth, tremor, anxiety. Serious: Liver damage (high doses/alcohol), seizures, respiratory depression, serotonin syndrome. Do not stop abruptly after prolonged use.', 'images/medicines/Tramal_Plus_Tablets_10s.jpeg', 1),
(91, 'Tramal SR 100mg Tablets', 'Tramadol HCl 100mg (Sustained Release)', 9, 9, 'Prescription', 'Tramal SR 100mg is a sustained-release formulation of Tramadol HCl that provides controlled, long-lasting pain relief over 12 hours. The extended-release technology ensures steady plasma levels, reducing the frequency of dosing and minimising peak-related side effects. Ideal for chronic pain management. Manufactured by Searle Pakistan.\n\n⚡ ADVANTAGES:\n• 12-hour sustained release — only 2 tablets per day needed\n• Steady blood levels reduce peaks/troughs and side effects\n• Effective for chronic pain conditions (arthritis, neuropathy, back pain)\n• Better compliance due to less frequent dosing\n• Reduced risk of breakthrough pain\n\n⚠️ DISADVANTAGES:\n• Higher dose (100mg) means greater dependence risk\n• Must be swallowed whole — crushing releases full dose at once (dangerous)\n• Not suitable for acute/sudden pain (slow onset)\n• Stronger side effects profile than immediate-release variants\n• Strict prescription control required', 'Take 1 tablet every 12 hours, or as prescribed. MUST be swallowed whole — do NOT crush, chew, or break the tablet as this destroys the sustained-release mechanism and releases the full dose at once, which is dangerous. Maximum: 400mg daily. Take with or without food. Not for children under 12.', 'Common: Nausea, dizziness, drowsiness, constipation, headache, fatigue. Less common: Sweating, dry mouth, indigestion, anxiety, tremor. Serious: Respiratory depression, seizures, serotonin syndrome, severe allergic reaction. High dependence potential — do not stop abruptly. Taper gradually under medical supervision.', 'images/medicines/Tramal_Sr_Tablets_10s.png', 1),
(92, 'Xanax 0.25mg Tablets', 'Alprazolam 0.25mg', 9, 4, 'Prescription', 'Xanax 0.25mg contains Alprazolam, a potent short-acting benzodiazepine used for the management of anxiety disorders, panic disorder, and anxiety associated with depression. It works by enhancing the effect of GABA (gamma-aminobutyric acid) neurotransmitter in the brain, producing a calming and sedative effect. Manufactured by Pfizer.\n\n⚡ ADVANTAGES:\n• Fast-acting anxiety relief (onset within 15-30 minutes)\n• Effective for panic attacks and generalised anxiety disorder (GAD)\n• Low starting dose (0.25mg) allows careful dose titration\n• One of the most widely prescribed and clinically studied benzodiazepines\n• Helps with anxiety-related insomnia\n\n⚠️ DISADVANTAGES:\n• HIGH risk of physical and psychological dependence (even at low doses)\n• Withdrawal can be severe and potentially dangerous — never stop abruptly\n• Causes drowsiness, impaired coordination, and memory issues\n• Dangerous when combined with alcohol or other CNS depressants\n• Intended for SHORT-TERM use only (2-4 weeks maximum recommended)\n• Controlled substance — strictly prescription-only', 'Take 1 tablet 2-3 times daily, or as directed by your psychiatrist/physician. Start with the lowest effective dose. Do not increase dose without medical advice. Do not drive or operate heavy machinery. Avoid alcohol completely. Do NOT stop suddenly — must be tapered gradually under doctor supervision.', 'Common: Drowsiness, fatigue, dizziness, light-headedness, impaired coordination, memory problems. Less common: Blurred vision, headache, nausea, dry mouth, changes in appetite, mood swings. Serious: Respiratory depression, paradoxical reactions (aggression, agitation), severe allergic reaction. Withdrawal symptoms (if stopped abruptly): Seizures, tremors, rebound anxiety, insomnia, psychosis.', 'images/medicines/Xanax_0_25mg_Tablets.png', 1),
(93, 'Xanax 0.5mg Tablets', 'Alprazolam 0.5mg', 9, 4, 'Prescription', 'Xanax 0.5mg is a higher-strength Alprazolam tablet for patients who require stronger anxiolytic (anti-anxiety) effect. Prescribed for moderate to severe anxiety disorders, panic disorder with or without agoraphobia, and short-term management of severe anxiety unresponsive to lower doses. Manufactured by Pfizer.\n\n⚡ ADVANTAGES:\n• Stronger anxiolytic effect for moderate-severe anxiety\n• Rapid onset provides quick relief during panic attacks\n• Effective for panic disorder with agoraphobia\n• Well-established safety profile when used as directed\n• Can be used as step-up from 0.25mg for patients needing higher dosage\n\n⚠️ DISADVANTAGES:\n• Higher dose = greater dependence and addiction risk\n• More pronounced sedation and cognitive impairment\n• Withdrawal at this dose is more severe and must be very carefully tapered\n• Not suitable for elderly patients or those with respiratory conditions\n• Strictly short-term use only — benzodiazepine dependence develops rapidly\n• Dangerous interactions with opioids, alcohol, and other sedatives', 'Take 1 tablet 2-3 times daily, or as prescribed by your psychiatrist. Do not exceed prescribed dose. Avoid alcohol, grapefruit juice, and CNS depressants. Do not drive or operate machinery. NEVER stop abruptly — dose must be reduced gradually over several weeks under strict medical supervision to prevent withdrawal seizures.', 'Common: Significant drowsiness, fatigue, dizziness, impaired coordination, cognitive dulling. Less common: Depression, confusion, blurred vision, gastrointestinal disturbances, weight changes. Serious: Respiratory depression (especially with opioids), paradoxical reactions, suicidal thoughts. Withdrawal (if stopped abruptly): Seizures, delirium, tremors, psychosis, rebound anxiety/panic.', 'images/medicines/Xanax_0_5mg_Tablets.jpeg', 1);
INSERT INTO `medicines` (`medicine_id`, `name`, `generic_name`, `category_id`, `brand_id`, `type`, `description`, `usage_info`, `side_effects`, `image_url`, `is_active`) VALUES
(94, 'Tonoflex-P Tablets', 'Tramadol HCl 37.5mg + Paracetamol 325mg', 9, 36, 'Prescription', 'Tonoflex-P is a combination analgesic by Sami Pharmaceuticals containing Tramadol HCl (37.5mg) and Paracetamol (325mg). It provides multimodal pain relief by combining an opioid analgesic with a non-opioid analgesic/antipyretic, making it effective for moderate to moderately severe pain while keeping individual drug doses low.\n\n⚡ ADVANTAGES:\n• Dual-action pain relief at lower individual doses\n• Effective for post-surgical, dental, orthopaedic, and musculoskeletal pain\n• Paracetamol adds fever-reducing capability\n• Cost-effective combination from trusted Pakistani manufacturer\n• 20-tablet pack size offers better value\n\n⚠️ DISADVANTAGES:\n• Contains opioid component — risk of dependence with prolonged use\n• Paracetamol limits total daily dose (liver toxicity risk above 4g/day)\n• Not recommended for patients with liver or kidney impairment\n• May cause drowsiness — affects driving ability\n• Should not be used with alcohol or other CNS depressants', 'Take 1-2 tablets every 4-6 hours as needed for pain. Maximum: 8 tablets per day. Do not exceed total paracetamol intake of 4g/day from all sources. Swallow whole with a glass of water. Can be taken with or without food. Avoid alcohol. Not for children under 12 years.', 'Common: Nausea, dizziness, drowsiness, constipation, headache. Less common: Vomiting, dry mouth, sweating, skin rash, fatigue. Serious: Liver damage (overdose/alcohol), seizures, respiratory depression, anaphylaxis. Risk of dependence. Taper gradually if discontinuing after prolonged use.', 'images/medicines/Tonoflex_P_Tablets_20s.png', 1),
(95, 'Lexotanil 3mg Tablets', 'Bromazepam 3mg', 9, 18, 'Prescription', 'Lexotanil 3mg contains Bromazepam, a benzodiazepine with anxiolytic (anti-anxiety), sedative, and muscle-relaxant properties. It is prescribed for the short-term treatment of severe anxiety states, tension, agitation, and anxiety-related insomnia. Marketed in Pakistan by Martin Dow Pharmaceuticals.\n\n⚡ ADVANTAGES:\n• Effective treatment for severe anxiety, tension, and agitation\n• Provides muscle relaxation in addition to anxiolytic effect\n• Helps with anxiety-related insomnia and sleep disturbances\n• Intermediate-acting — balanced onset and duration\n• Well-established safety profile in short-term use (up to 4 weeks)\n\n⚠️ DISADVANTAGES:\n• HIGH risk of physical and psychological dependence\n• Must NOT be stopped abruptly — requires gradual tapering\n• Causes drowsiness, impaired concentration, and reduced reflexes\n• Dangerous with alcohol and other CNS depressants\n• Intended for SHORT-TERM use only (maximum 4 weeks recommended)\n• Controlled substance — strict prescription requirements\n• Not suitable for patients with myasthenia gravis or respiratory insufficiency', 'Take 1 tablet 1-3 times daily, or as directed by your psychiatrist/physician. For anxiety: 1.5mg-3mg up to 3 times daily. For severe anxiety: up to 6mg-12mg daily in divided doses. Swallow whole with water. Do not drive or operate machinery. Avoid alcohol completely. Do NOT stop suddenly after regular use — must be tapered gradually over weeks.', 'Common: Drowsiness, sedation, fatigue, dizziness, muscle weakness, impaired coordination. Less common: Headache, confusion, dry mouth, blurred vision, gastrointestinal upset. Serious: Respiratory depression, paradoxical reactions (aggression, excitability), amnesia. Withdrawal (if stopped abruptly): Seizures, tremors, insomnia, anxiety, hallucinations, psychosis. Long-term use may cause cognitive impairment and emotional blunting.', 'images/medicines/Lexotanil_3mg_Tablets_1.png', 1);

-- --------------------------------------------------------

--
-- Table structure for table `medicine_variants`
--

CREATE TABLE `medicine_variants` (
  `variant_id` int(11) NOT NULL,
  `medicine_id` int(11) NOT NULL,
  `pack_size` varchar(50) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `stock_qty` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `medicine_variants`
--

INSERT INTO `medicine_variants` (`variant_id`, `medicine_id`, `pack_size`, `price`, `stock_qty`) VALUES
(1, 1, 'Strip of 10', 35.00, 200),
(2, 2, 'Strip of 10', 42.00, 150),
(3, 3, 'Strip of 10', 35.00, 150),
(4, 4, 'Strip of 10', 35.00, 149),
(5, 5, 'Strip of 10', 30.00, 200),
(6, 6, 'Strip of 10', 60.00, 100),
(7, 7, 'Strip of 10', 45.00, 99),
(8, 8, 'Strip of 10', 125.00, 80),
(9, 9, 'Tube of 20g', 350.00, 60),
(10, 10, 'Strip of 10', 125.00, 80),
(11, 11, 'Strip of 10', 315.00, 60),
(12, 12, 'Strip of 10', 100.00, 70),
(13, 13, 'Strip of 10', 40.00, 100),
(14, 14, 'Strip of 10', 70.00, 80),
(15, 15, 'Strip of 10', 350.00, 50),
(16, 16, 'Strip of 10', 210.00, 68),
(17, 17, 'Strip of 10', 80.00, 98),
(18, 18, 'Strip of 10', 140.00, 98),
(19, 19, 'Strip of 5', 65.00, 100),
(20, 20, 'Strip of 10', 100.00, 100),
(21, 21, 'Strip of 6', 380.00, 59),
(22, 22, 'Strip of 10', 180.00, 78),
(23, 23, 'Strip of 10', 850.00, 40),
(24, 24, 'Strip of 6', 350.00, 60),
(25, 25, 'Strip of 10', 250.00, 60),
(26, 26, 'Strip of 10', 220.00, 60),
(27, 27, 'Strip of 5', 450.00, 50),
(28, 28, 'Strip of 10', 150.00, 60),
(29, 29, 'Strip of 10', 170.00, 60),
(30, 30, 'Strip of 10', 220.00, 57),
(31, 31, 'Strip of 10', 90.00, 100),
(32, 32, 'Strip of 14', 1400.00, 34),
(33, 33, 'Strip of 14', 950.00, 30),
(34, 34, 'Strip of 10', 250.00, 50),
(35, 35, 'Strip of 10', 180.00, 60),
(36, 36, 'Strip of 10', 60.00, 79),
(37, 37, 'Strip of 10', 280.00, 50),
(38, 38, 'Strip of 20', 150.00, 100),
(39, 39, 'Strip of 10', 200.00, 80),
(40, 40, 'Strip of 10', 180.00, 70),
(41, 41, 'Strip of 10', 150.00, 80),
(42, 42, 'Bottle of 30', 2200.00, 29),
(43, 43, 'Strip of 20', 140.00, 80),
(44, 44, 'Bottle of 30', 750.00, 40),
(45, 45, 'Strip of 10', 150.00, 100),
(46, 46, 'Strip of 10', 90.00, 78),
(47, 47, 'Bottle of 120ml', 220.00, 55),
(48, 48, 'Strip of 10', 45.00, 100),
(49, 49, 'Strip of 10', 30.00, 100),
(50, 50, 'Strip of 10', 120.00, 78),
(51, 51, 'Pack of 6', 90.00, 99),
(52, 52, 'Pack of 20 vials', 750.00, 40),
(53, 53, 'Strip of 14', 550.00, 50),
(54, 54, 'Strip of 10', 90.00, 80),
(55, 55, 'Strip of 20', 180.00, 70),
(56, 56, 'Strip of 14', 250.00, 59),
(57, 57, 'Strip of 10', 200.00, 60),
(58, 58, 'Tube of 20g', 280.00, 50),
(59, 59, 'Tube of 25g', 300.00, 50),
(60, 60, 'Tube of 15g', 250.00, 49),
(61, 61, 'Tube of 10g', 150.00, 60),
(62, 62, 'Tube of 20g', 220.00, 60),
(63, 63, 'Tube of 20g', 350.00, 50),
(64, 64, 'Pack of 50g', 250.00, 80),
(65, 65, 'Bottle of 300ml', 650.00, 60),
(66, 66, 'Box of 175g', 550.00, 60),
(67, 67, 'Box of 175g', 580.00, 59),
(68, 68, 'Tin of 400g', 1450.00, 50),
(69, 69, 'Bottle of 15ml', 180.00, 70),
(70, 70, 'Pack of 30', 90.00, 28),
(71, 71, 'Strip of 10', 120.00, 49),
(72, 72, '1 Unit', 3449.00, 25),
(73, 73, '1 Unit', 4500.00, 50),
(74, 74, '1 Unit', 4200.00, 48),
(75, 75, '1 Unit', 1800.00, 50),
(76, 76, '1 Unit', 3800.00, 50),
(77, 77, '150ml Spray', 650.00, 38),
(78, 78, '150ml Spray', 750.00, 33),
(79, 79, '120ml Spray', 550.00, 45),
(80, 80, '200ml Spray', 450.00, 50),
(81, 81, '150ml Spray', 850.00, 30),
(82, 82, '200ml Spray', 800.00, 25),
(83, 83, '120ml Spray', 580.00, 35),
(84, 84, '120ml Spray', 580.00, 30),
(85, 85, '120ml Spray', 580.00, 30),
(86, 86, '120ml Spray', 580.00, 35),
(87, 87, '30ml Bottle', 1850.00, 20),
(88, 88, '50ml Tube', 950.00, 25),
(89, 89, '10 Capsules', 250.00, 29),
(90, 90, '10 Tablets', 240.00, 25),
(91, 91, '10 Tablets', 370.00, 19),
(92, 92, '30 Tablets', 185.00, 35),
(93, 93, '30 Tablets', 200.00, 30),
(94, 94, '20 Tablets', 480.00, 38),
(95, 95, '50 Tablets', 635.00, 30);

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `notification_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `type` enum('prescription_approved','prescription_rejected','order_update','system') DEFAULT 'system',
  `title` varchar(255) NOT NULL,
  `message` text DEFAULT NULL,
  `link` varchar(500) DEFAULT NULL,
  `icon` varchar(50) DEFAULT 'notifications',
  `is_read` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `notifications`
--

INSERT INTO `notifications` (`notification_id`, `user_id`, `type`, `title`, `message`, `link`, `icon`, `is_read`, `created_at`) VALUES
(1, 18, 'order_update', 'Order #0023 Confirmed', 'Your order has been confirmed and is currently being prepared.', '/customer/orders', 'fact_check', 1, '2026-07-24 16:00:41'),
(2, 18, 'order_update', 'Order #0023 Packed 📦', 'Your order has been packed by our pharmacist and is waiting for delivery.', '/customer/orders', 'inventory_2', 1, '2026-07-24 16:01:23'),
(3, 18, 'order_update', 'Order #0023 Shipped 🚚', 'Your order is on its way!', '/customer/orders', 'local_shipping', 1, '2026-07-24 16:07:33'),
(4, 18, 'order_update', 'Order #0023 Delivered 🎉', 'Your order has been delivered successfully. Thank you for choosing SehatHub!', '/customer/orders', 'done_all', 1, '2026-07-24 16:07:54'),
(5, 18, 'prescription_rejected', 'Prescription #12 Rejected', 'Reason: picture no clear', '/customer/prescriptions', 'error', 1, '2026-07-24 16:23:13'),
(6, 18, 'prescription_rejected', 'Prescription #13 Rejected', 'Reason: not clear', '/customer/prescriptions', 'error', 1, '2026-07-24 16:25:15'),
(7, 18, 'prescription_approved', 'Prescription #14 Approved ✅', 'Your prescription has been verified. You can now order the prescribed medicines.', '/customer/prescriptions', 'task_alt', 1, '2026-07-24 16:40:12'),
(8, 18, 'order_update', 'Order #0024 Confirmed', 'Your order has been confirmed and is currently being prepared.', '/customer/orders', 'fact_check', 1, '2026-07-24 16:40:40'),
(9, 18, 'order_update', 'Order #0024 Packed 📦', 'Your order has been packed by our pharmacist and is waiting for delivery.', '/customer/orders', 'inventory_2', 1, '2026-07-24 16:41:09'),
(10, 18, 'order_update', 'Order #0024 Shipped 🚚', 'Your order is on its way!', '/customer/orders', 'local_shipping', 1, '2026-07-24 16:41:22'),
(11, 18, 'order_update', 'Order #0024 Delivered 🎉', 'Your order has been delivered successfully. Thank you for choosing SehatHub!', '/customer/orders', 'done_all', 1, '2026-07-24 16:41:32'),
(12, 18, 'prescription_rejected', 'Prescription #15 Rejected', 'Reason: Upload prescription related to this medicine', '/customer/prescriptions', 'error', 1, '2026-07-24 16:43:10'),
(13, 18, 'order_update', 'Order #0025 Cancelled ❌', 'Your order was cancelled by the pharmacist. Reason: not proper precription uploded by customer', '/customer/orders', 'cancel', 1, '2026-07-24 16:44:04'),
(14, 18, 'prescription_rejected', 'Prescription #16 Rejected', 'Reason: not accepted', '/customer/prescriptions', 'error', 1, '2026-07-24 16:44:39'),
(15, 16, 'order_update', 'Order #0026 Confirmed', 'Your order has been confirmed and is currently being prepared.', '/customer/orders', 'fact_check', 1, '2026-07-27 17:18:13'),
(16, 16, 'order_update', 'Order #0026 Packed 📦', 'Your order has been packed by our pharmacist and is waiting for delivery.', '/customer/orders', 'inventory_2', 1, '2026-07-27 17:18:26'),
(17, 16, 'order_update', 'Order #0027 Confirmed', 'Your order has been confirmed and is currently being prepared.', '/customer/orders', 'fact_check', 1, '2026-07-27 17:18:29'),
(18, 16, 'order_update', 'Order #0027 Packed 📦', 'Your order has been packed by our pharmacist and is waiting for delivery.', '/customer/orders', 'inventory_2', 1, '2026-07-27 17:18:31'),
(19, 16, 'order_update', 'Order #0026 Shipped 🚚', 'Your order is on its way!', '/customer/orders', 'local_shipping', 1, '2026-07-27 17:19:30'),
(20, 16, 'order_update', 'Order #0027 Shipped 🚚', 'Your order is on its way!', '/customer/orders', 'local_shipping', 1, '2026-07-27 17:19:32'),
(21, 16, 'order_update', 'Order #0027 Delivered 🎉', 'Your order has been delivered successfully. Thank you for choosing SehatHub!', '/customer/orders', 'done_all', 1, '2026-07-27 17:19:36'),
(22, 16, 'order_update', 'Order #0026 Delivered 🎉', 'Your order has been delivered successfully. Thank you for choosing SehatHub!', '/customer/orders', 'done_all', 1, '2026-07-27 17:19:37'),
(23, 16, 'order_update', 'Order #0028 Confirmed', 'Your order has been confirmed and is currently being prepared.', '/customer/orders', 'fact_check', 1, '2026-08-02 13:19:50'),
(24, 17, 'prescription_approved', 'Prescription #17 Approved ✅', 'Your prescription has been verified. You can now order the prescribed medicines.', '/customer/prescriptions', 'task_alt', 1, '2026-08-02 13:19:56'),
(25, 16, 'order_update', 'Order #0029 Confirmed', 'Your order has been confirmed and is currently being prepared.', '/customer/orders', 'fact_check', 1, '2026-08-02 13:20:09'),
(26, 16, 'order_update', 'Order #0028 Packed 📦', 'Your order has been packed by our pharmacist and is waiting for delivery.', '/customer/orders', 'inventory_2', 1, '2026-08-02 13:20:11'),
(27, 16, 'order_update', 'Order #0029 Packed 📦', 'Your order has been packed by our pharmacist and is waiting for delivery.', '/customer/orders', 'inventory_2', 1, '2026-08-02 13:20:12'),
(28, 17, 'order_update', 'Order #0030 Confirmed', 'Your order has been confirmed and is currently being prepared.', '/customer/orders', 'fact_check', 1, '2026-08-02 13:20:14'),
(29, 17, 'order_update', 'Order #0030 Packed 📦', 'Your order has been packed by our pharmacist and is waiting for delivery.', '/customer/orders', 'inventory_2', 1, '2026-08-02 13:20:16'),
(30, 16, 'order_update', 'Order #0028 Shipped 🚚', 'Your order is on its way!', '/customer/orders', 'local_shipping', 1, '2026-08-02 13:21:22'),
(31, 16, 'order_update', 'Order #0029 Shipped 🚚', 'Your order is on its way!', '/customer/orders', 'local_shipping', 1, '2026-08-02 13:21:25'),
(32, 17, 'order_update', 'Order #0030 Shipped 🚚', 'Your order is on its way!', '/customer/orders', 'local_shipping', 1, '2026-08-02 13:21:26'),
(33, 16, 'order_update', 'Order #0028 Delivered 🎉', 'Your order has been delivered successfully. Thank you for choosing SehatHub!', '/customer/orders', 'done_all', 1, '2026-08-02 13:21:28'),
(34, 16, 'order_update', 'Order #0029 Delivered 🎉', 'Your order has been delivered successfully. Thank you for choosing SehatHub!', '/customer/orders', 'done_all', 1, '2026-08-02 13:21:30'),
(35, 17, 'order_update', 'Order #0030 Delivered 🎉', 'Your order has been delivered successfully. Thank you for choosing SehatHub!', '/customer/orders', 'done_all', 1, '2026-08-02 13:21:31'),
(36, 11, 'order_update', 'Order #0031 Confirmed', 'Your order has been confirmed and is currently being prepared.', '/customer/orders', 'fact_check', 0, '2026-08-03 05:22:06'),
(37, 11, 'order_update', 'Order #0031 Packed 📦', 'Your order has been packed by our pharmacist and is waiting for delivery.', '/customer/orders', 'inventory_2', 0, '2026-08-03 05:22:09'),
(38, 13, 'order_update', 'Order #0032 Confirmed', 'Your order has been confirmed and is currently being prepared.', '/customer/orders', 'fact_check', 0, '2026-08-03 05:46:56'),
(39, 17, 'order_update', 'Order #0037 Cancelled', 'You successfully cancelled this order.', '/customer/orders', 'cancel', 1, '2026-08-10 12:49:51'),
(40, 13, 'prescription_rejected', 'Prescription #18 Rejected', 'Reason: not clear picture', '/customer/prescriptions', 'error', 0, '2026-10-16 15:16:03'),
(41, 11, 'order_update', 'Order #0031 Shipped 🚚', 'Your order is on its way!', '/customer/orders', 'local_shipping', 0, '2026-10-16 15:18:07'),
(42, 11, 'order_update', 'Order #0031 Delivered 🎉', 'Your order has been delivered successfully. Thank you for choosing SehatHub!', '/customer/orders', 'done_all', 0, '2026-10-16 15:18:37'),
(43, 9, 'order_update', 'Order #0033 Confirmed', 'Your order has been confirmed and is currently being prepared.', '/customer/orders', 'fact_check', 0, '2026-10-16 15:19:05'),
(44, 9, 'order_update', 'Order #0033 Packed 📦', 'Your order has been packed by our pharmacist and is waiting for delivery.', '/customer/orders', 'inventory_2', 0, '2026-10-16 15:19:12');

-- --------------------------------------------------------

--
-- Table structure for table `orders`
--

CREATE TABLE `orders` (
  `order_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `status` enum('placed','confirmed','packed','shipped','delivered','cancelled') NOT NULL DEFAULT 'placed',
  `cancellation_reason` text DEFAULT NULL,
  `delivery_address` varchar(255) NOT NULL,
  `special_instructions` text DEFAULT NULL,
  `payment_method` enum('cash_on_delivery','card','easypaisa','jazzcash') DEFAULT 'cash_on_delivery',
  `delivery_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `orders`
--

INSERT INTO `orders` (`order_id`, `customer_id`, `total_amount`, `status`, `cancellation_reason`, `delivery_address`, `special_instructions`, `payment_method`, `delivery_id`, `created_at`) VALUES
(1, 5, 240.00, 'delivered', NULL, 'obaid shah, tarlai, islamabad | Phone: 03015051571', NULL, 'cash_on_delivery', NULL, '2026-07-02 09:12:33'),
(2, 5, 310.00, 'delivered', NULL, 'obaid shah, tarlai, islamabad | Phone: 03015051571', NULL, 'cash_on_delivery', NULL, '2026-07-02 09:29:08'),
(3, 7, 310.00, 'delivered', NULL, 'obaid shah, tarlai, islamabad | Phone: 03015051571', NULL, 'cash_on_delivery', NULL, '2026-07-04 17:07:44'),
(4, 8, 190.00, 'delivered', NULL, 'taban, tarlai, islamabad | Phone: 03015051571', NULL, 'cash_on_delivery', NULL, '2026-07-05 11:34:20'),
(5, 8, 320.00, 'delivered', NULL, 'taban, tarlai, islamabad | Phone: 03015051571', NULL, 'cash_on_delivery', NULL, '2026-07-07 21:16:13'),
(6, 8, 280.00, 'delivered', NULL, 'taban, tamari chowk, islamabad | Phone: 03128556552', NULL, 'cash_on_delivery', NULL, '2026-07-18 13:02:29'),
(7, 12, 220.00, 'delivered', NULL, 'SFGS, ISLAMABAD, ISLAMABAD | Phone: 00312313144', NULL, 'cash_on_delivery', NULL, '2026-07-19 06:58:56'),
(8, 12, 320.00, 'delivered', NULL, 'SFGS, RRERW, WRER | Phone: 4234242', NULL, 'cash_on_delivery', NULL, '2026-07-19 07:07:15'),
(9, 12, 850.00, 'delivered', NULL, 'SFGS, 45, 464 | Phone: 43634635654', NULL, 'cash_on_delivery', NULL, '2026-07-19 07:29:58'),
(10, 12, 220.00, 'delivered', NULL, 'SFGS, tamaari chowk, Islamabad | Phone: 03124232133', NULL, 'cash_on_delivery', NULL, '2026-07-19 11:33:48'),
(11, 12, 350.00, 'delivered', NULL, 'SFGS, tamaari chowk, Islamabad | Phone: 03128556552', NULL, 'cash_on_delivery', NULL, '2026-07-20 13:41:05'),
(12, 12, 2340.00, 'delivered', NULL, 'SFGS, tamaari chowk, Islamabad | Phone: 03124232332', NULL, 'cash_on_delivery', NULL, '2026-07-20 14:03:18'),
(13, 12, 280.00, 'delivered', NULL, 'SFGS, tamaari chowk, Islamabad | Phone: 03128556552', NULL, 'cash_on_delivery', NULL, '2026-07-20 14:08:22'),
(14, 12, 220.00, 'delivered', NULL, 'obaid, tamaari chowk, Islamabad | Phone: 03128556552', NULL, 'cash_on_delivery', NULL, '2026-07-20 14:14:26'),
(15, 12, 540.00, 'delivered', NULL, 'SFGS, tamaari chowk, rawalpindi | Phone: 03124232112', NULL, 'cash_on_delivery', NULL, '2026-07-20 14:28:03'),
(16, 8, 160.00, 'delivered', NULL, 'taban, Sadiqabad, Lahore | Phone: 03124324324', NULL, 'cash_on_delivery', NULL, '2026-07-20 16:14:14'),
(17, 12, 480.00, 'delivered', NULL, 'SFGS, Gulshan road, Karachi | Phone: 03142344123', NULL, 'cash_on_delivery', NULL, '2026-07-20 16:20:18'),
(18, 12, 190.00, 'delivered', NULL, 'tt, Gulshan road, Karachi | Phone: 03013244553', NULL, 'cash_on_delivery', NULL, '2026-07-21 07:36:41'),
(19, 11, 3349.00, 'delivered', NULL, 'test, ghouri garden, Islamabad | Phone: 03115403230', 'donot ring the bell and wait for response', 'cash_on_delivery', NULL, '2026-07-22 11:49:57'),
(20, 11, 850.00, 'delivered', NULL, 'test, ghouri garden, peshawar | Phone: 03015051571', NULL, 'cash_on_delivery', NULL, '2026-07-23 20:19:09'),
(21, 11, 280.00, 'delivered', NULL, 'Ali, Mirzapur, Quetta | Phone: 03128543231', NULL, 'cash_on_delivery', NULL, '2026-07-24 10:30:35'),
(22, 11, 180.00, 'delivered', NULL, 'Arslan, AHMEDABAD, Multan | Phone: 03123123416', NULL, 'cash_on_delivery', NULL, '2026-07-24 10:46:07'),
(23, 13, 750.00, 'delivered', NULL, 'Sikander, Tarlai Kalan, Hydrabad | Phone: 03210421421', NULL, 'cash_on_delivery', NULL, '2026-07-24 16:00:11'),
(24, 13, 190.00, 'delivered', NULL, 'Final Testing, Tarlai Kalan, islamabad | Phone: 03210421421', NULL, 'cash_on_delivery', NULL, '2026-07-24 16:39:54'),
(25, 13, 220.00, 'cancelled', 'not proper precription uploded by customer', 'Final Testing, Tarlai Kalan, islamabad | Phone: 03210421421', NULL, 'cash_on_delivery', NULL, '2026-07-24 16:42:34'),
(26, 11, 4200.00, 'delivered', NULL, 'test, AHMEDABAD, Multan | Phone: 03123123416', NULL, 'cash_on_delivery', NULL, '2026-07-27 17:16:43'),
(27, 11, 4200.00, 'delivered', NULL, 'test, AHMEDABAD, Multan | Phone: 03123123416', NULL, 'cash_on_delivery', NULL, '2026-07-27 17:17:06'),
(28, 11, 320.00, 'delivered', NULL, 'test, AHMEDABAD, Multan | Phone: 03123123416', NULL, 'cash_on_delivery', NULL, '2026-07-29 11:19:16'),
(29, 11, 350.00, 'delivered', NULL, 'ahmed, AHMEDABAD, Multan | Phone: 03123123416', NULL, 'cash_on_delivery', NULL, '2026-08-02 13:00:58'),
(30, 12, 1000.00, 'delivered', NULL, 'arslan, Gulshan road, Karachi | Phone: 03128556553', NULL, 'cash_on_delivery', NULL, '2026-08-02 13:03:05'),
(31, 8, 145.00, 'delivered', NULL, 'Fatima, Sadiqabad, KPK | Phone: 03123294221', NULL, 'cash_on_delivery', NULL, '2026-08-02 13:22:18'),
(32, 10, 470.00, 'confirmed', NULL, 'Sikander, Tamma, Islamabad | Phone: 03015051571', NULL, 'cash_on_delivery', NULL, '2026-08-02 13:38:21'),
(33, 6, 320.00, 'packed', NULL, 'obaid shah, khanna pull, Islamabad | Phone: 03015032435', NULL, 'cash_on_delivery', NULL, '2026-08-03 05:28:19'),
(34, 12, 190.00, 'placed', NULL, 'Fahad, Gulshan road, Karachi | Phone: 03125465778', NULL, 'cash_on_delivery', NULL, '2026-08-03 05:33:17'),
(35, 11, 540.00, 'placed', NULL, 'test, AHMEDABAD, Multan | Phone: 03123123416', NULL, 'cash_on_delivery', NULL, '2026-08-03 06:03:55'),
(36, 11, 225.00, 'placed', NULL, 'test, AHMEDABAD, Multan | Phone: 03123123416', NULL, 'cash_on_delivery', NULL, '2026-08-03 08:36:56'),
(37, 12, 3650.00, 'cancelled', 'Cancelled by customer', 'SFGS, Gulshan road, Karachi | Phone: 03125465778', NULL, 'cash_on_delivery', NULL, '2026-08-10 12:49:39'),
(38, 5, 850.00, 'placed', NULL, 'obaid shah, tarlai, islamabad | Phone: 03015051571', NULL, 'cash_on_delivery', NULL, '2026-10-16 15:10:18');

-- --------------------------------------------------------

--
-- Table structure for table `order_items`
--

CREATE TABLE `order_items` (
  `order_item_id` int(11) NOT NULL,
  `order_id` int(11) NOT NULL,
  `variant_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  `price_at_purchase` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `order_items`
--

INSERT INTO `order_items` (`order_item_id`, `order_id`, `variant_id`, `quantity`, `price_at_purchase`) VALUES
(1, 1, 18, 1, 140.00),
(2, 2, 16, 1, 210.00),
(3, 3, 16, 1, 210.00),
(4, 4, 70, 1, 90.00),
(5, 5, 30, 1, 220.00),
(6, 6, 22, 1, 180.00),
(7, 7, 71, 1, 120.00),
(8, 8, 30, 1, 220.00),
(9, 9, 67, 1, 580.00),
(10, 9, 51, 1, 90.00),
(11, 9, 17, 1, 80.00),
(12, 10, 50, 1, 120.00),
(13, 11, 60, 1, 250.00),
(14, 12, 18, 1, 140.00),
(15, 12, 42, 1, 2200.00),
(16, 13, 46, 1, 90.00),
(17, 13, 70, 1, 90.00),
(18, 14, 50, 1, 120.00),
(19, 15, 47, 2, 220.00),
(20, 16, 36, 1, 60.00),
(21, 17, 21, 1, 380.00),
(22, 18, 70, 1, 90.00),
(23, 19, 72, 1, 3349.00),
(24, 20, 78, 1, 750.00),
(25, 21, 22, 1, 180.00),
(26, 22, 17, 1, 80.00),
(27, 23, 77, 1, 650.00),
(28, 24, 70, 1, 90.00),
(29, 25, 71, 1, 120.00),
(30, 26, 74, 1, 4200.00),
(31, 27, 74, 1, 4200.00),
(32, 28, 30, 1, 220.00),
(33, 29, 56, 1, 250.00),
(34, 30, 77, 1, 650.00),
(35, 30, 89, 1, 250.00),
(36, 31, 7, 1, 45.00),
(37, 32, 91, 1, 370.00),
(38, 33, 47, 1, 220.00),
(39, 34, 46, 1, 90.00),
(40, 35, 47, 2, 220.00),
(41, 36, 4, 1, 35.00),
(42, 36, 70, 1, 90.00),
(43, 37, 68, 1, 1450.00),
(44, 37, 42, 1, 2200.00),
(45, 38, 78, 1, 750.00);

-- --------------------------------------------------------

--
-- Table structure for table `pharmacists`
--

CREATE TABLE `pharmacists` (
  `pharmacist_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `license_number` varchar(50) NOT NULL,
  `branch` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `pharmacists`
--

INSERT INTO `pharmacists` (`pharmacist_id`, `user_id`, `license_number`, `branch`) VALUES
(2, 10, 'PHM-2026-0001', 'Islamabad Main Branch');

-- --------------------------------------------------------

--
-- Table structure for table `prescriptions`
--

CREATE TABLE `prescriptions` (
  `prescription_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `order_id` int(11) DEFAULT NULL,
  `image_path` varchar(255) NOT NULL,
  `status` enum('pending','approved','rejected') DEFAULT 'pending',
  `uploaded_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `rejection_reason` varchar(255) DEFAULT NULL,
  `customer_seen` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `prescriptions`
--

INSERT INTO `prescriptions` (`prescription_id`, `customer_id`, `order_id`, `image_path`, `status`, `uploaded_at`, `rejection_reason`, `customer_seen`) VALUES
(1, 6, NULL, 'uploads/prescriptions/customer6_1783026290_aab_e_hayat.jpg', 'approved', '2026-07-02 21:04:50', NULL, 1),
(2, 6, NULL, 'uploads/prescriptions/customer6_1783186507_Notes_BW.jpeg', 'rejected', '2026-07-04 17:35:07', NULL, 1),
(3, 8, 4, 'uploads/prescriptions/customer8_1783251003_Board_Backside.jpeg', 'approved', '2026-07-05 11:30:03', NULL, 1),
(4, 9, NULL, 'uploads/prescriptions/customer9_1783270951_aab_e_hayat.jpg', 'approved', '2026-07-05 17:02:31', NULL, 1),
(5, 8, NULL, 'uploads/prescriptions/customer8_1784442822_IMG_20251230_210631.jpg', 'approved', '2026-07-19 06:33:42', NULL, 1),
(6, 10, NULL, 'uploads/prescriptions/customer10_1784443586_IMG_20251230_210631.jpg', 'rejected', '2026-07-19 06:46:26', 'image is not related to medicine', 1),
(7, 10, NULL, 'uploads/prescriptions/customer10_1784443815_IMG-20251120-WA0027.jpg', 'approved', '2026-07-19 06:50:15', NULL, 1),
(8, 11, NULL, 'uploads/prescriptions/customer11_1784444042_IMG-20251120-WA0027.jpg', 'approved', '2026-07-19 06:54:02', NULL, 1),
(9, 12, 7, 'uploads/prescriptions/customer12_1784444263_IMG-20221229-WA0016.jpg', 'approved', '2026-07-19 06:57:43', NULL, 1),
(10, 12, 13, 'uploads/prescriptions/customer12_1784556417_IMG-20221229-WA0016.jpg', 'approved', '2026-07-20 14:06:57', NULL, 1),
(11, 12, 18, 'uploads/prescriptions/customer12_1784619335_IMG-20221229-WA0016.jpg', 'approved', '2026-07-21 07:35:35', NULL, 1),
(12, 13, NULL, 'uploads/prescriptions/customer13_1784909560_20250905_000640.jpg', 'rejected', '2026-07-24 16:12:40', 'picture no clear', 1),
(13, 13, NULL, 'uploads/prescriptions/customer13_1784910237_20250905_0145181.jpg', 'rejected', '2026-07-24 16:23:57', 'not clear', 1),
(14, 13, 24, 'uploads/prescriptions/customer13_1784911177_20250905_014520.jpg', 'approved', '2026-07-24 16:39:37', NULL, 1),
(15, 13, 25, 'uploads/prescriptions/customer13_1784911345_20250624_192700.jpg', 'rejected', '2026-07-24 16:42:25', 'Upload prescription related to this medicine', 1),
(16, 13, NULL, 'uploads/prescriptions/customer13_1784911410_20250624_192700.jpg', 'rejected', '2026-07-24 16:43:30', 'not accepted', 0),
(17, 12, 30, 'uploads/prescriptions/customer12_1785675758_Screenshot_2026-07-21_200516.png', 'approved', '2026-08-02 13:02:38', NULL, 1),
(18, 10, 32, 'uploads/prescriptions/customer10_1785677864_courage.jpg', 'rejected', '2026-08-02 13:37:44', 'not clear picture', 0),
(19, 11, 36, 'uploads/prescriptions/customer11_1785746156_48lawspower.jpg', 'pending', '2026-08-03 08:35:56', NULL, 1);

-- --------------------------------------------------------

--
-- Table structure for table `reviews`
--

CREATE TABLE `reviews` (
  `review_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `medicine_id` int(11) NOT NULL,
  `rating` int(11) NOT NULL CHECK (`rating` between 1 and 5),
  `comment` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `saved_items`
--

CREATE TABLE `saved_items` (
  `saved_item_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `variant_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  `saved_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `saved_items`
--

INSERT INTO `saved_items` (`saved_item_id`, `customer_id`, `variant_id`, `quantity`, `saved_at`) VALUES
(4, 8, 51, 1, '2026-08-02 13:40:18');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `role` enum('customer','pharmacist','admin','delivery') NOT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `username` varchar(50) DEFAULT NULL,
  `reset_token` varchar(64) DEFAULT NULL,
  `reset_token_expiry` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `full_name`, `email`, `password_hash`, `phone`, `role`, `is_active`, `created_at`, `username`, `reset_token`, `reset_token_expiry`) VALUES
(1, 'Ahmed Khan', 'ahmed.khan@gmail.com', 'placeholder_hash_1', '03001234567', 'customer', 1, '2026-06-28 12:27:22', NULL, NULL, NULL),
(2, 'Sara Malik', 'sara.malik@gmail.com', 'placeholder_hash_2', '03021234567', 'customer', 1, '2026-06-28 12:27:22', NULL, NULL, NULL),
(3, 'Bilal Ahmed', 'bilal.ahmed@gmail.com', 'placeholder_hash_3', '03331234567', 'customer', 1, '2026-06-28 12:27:22', NULL, NULL, NULL),
(6, 'Faisal Iqbal', 'faisal.delivery@sehathub.com', 'placeholder_hash_6', '03211234567', 'delivery', 1, '2026-06-28 12:27:22', NULL, NULL, NULL),
(7, 'test', 'test@gmail.com', '$2b$12$uwALy44eSCpl.lzvO6Vub.BvI1X2UOEliG.RyJgaxINS0r4kvsrQa', '03123213231', 'customer', 1, '2026-06-28 13:20:58', NULL, NULL, NULL),
(8, 'obaid shah', 'obaidshah150@gmail.com', '$2b$12$IGbalLH5y3UnMpw1q8WOsOX.fR3wRVNCUjwEQ4ws592X4ZUUGCcNy', '03015051571', 'customer', 1, '2026-06-30 12:03:23', NULL, NULL, NULL),
(9, 'obaid shah', 'obaidshah@gmail.com', '$2b$12$mZw98fe6CoOUxgsNGi6tL.JELEMz./UKASlJfVdjDeWIcHjRPg..C', '03015032435', 'customer', 1, '2026-07-02 20:40:32', NULL, NULL, NULL),
(10, 'obaid shah', 'pharmacist.test@sehathub.com', '$2b$12$VYF2bu/tXBPg5DFAumIHtuM3ehHP/s.QlXXvEyGYdNxEubiWWIJzq', '03015051571', 'pharmacist', 1, '2026-07-04 16:50:42', NULL, NULL, NULL),
(11, 'taban', 'tabanshah@gmail.com', '$2b$12$hFShMzKkSJuGZuK98pQmru6KR0aSCRG3AinOXks8EzR7awUTnNL2e', NULL, 'customer', 1, '2026-07-05 11:20:52', NULL, NULL, NULL),
(12, 'TEST', 'test1@gmail.com', '$2b$12$z.ONaJ.iDhzTVXRSqhZoLuWTW.FlGWcleoZaT6F1Z4QaJO8l61ugO', '03015051571', 'customer', 1, '2026-07-05 17:01:57', NULL, NULL, NULL),
(13, 'Ahmed', 'testing@sehathub.com', '$2b$12$lpJuwGlnT0AavrMVMAk/r.ddls1MbKqvE7/CLgkF7EmVshAV0.Z8q', '03015051543', 'customer', 0, '2026-07-07 06:02:20', NULL, NULL, NULL),
(14, 'Admin User', 'admin', '$2b$12$Jey6Cet6koolZ0jWuh0qgOBhz2DqNee65bSRnivdQfKhFPvpyhWrm', '03000000000', 'admin', 1, '2026-07-07 21:00:42', NULL, NULL, NULL),
(15, 'Test Delivery Manager', 'delivery.test@sehathub.com', '$2b$12$EiVqTpx6SBsPms8Ohxrtk.eEjpi2d9VHfDGiNbHmDnkmDkjP/bDJ2', '03009998877', 'delivery', 1, '2026-07-11 05:58:31', NULL, NULL, NULL),
(16, 'test', 'obaidshah222@gmail.com', '$2b$12$DF4ALRj8xzG5Lo3kH5ZJBengc107q3zPXGpBG6x3UikEq7Tr4Wyx.', '03123123416', 'customer', 1, '2026-07-19 06:53:40', NULL, NULL, NULL),
(17, 'SFGS', 'obaidshah2232@gmail.com', '$2b$12$T0h.lA6Os/Z/..8g/cWxvOc46EaP/wrOx.vg4cnK0vwINW5XApfnS', '03125465778', 'customer', 1, '2026-07-19 06:56:56', NULL, 's3Lgd526B4J976C1Rfcf_x7Tp6aIrR_xfEiUPwzxjDQ', '2026-07-19 17:25:17'),
(18, 'Final Testing', 'finaltesting@sehathub.com', '$2b$12$7ta85LZVo9ahCMFNhZRZu.hSM9iceHmUkN3B.FilJbcyjyb2gBjTy', '03210421421', 'customer', 1, '2026-07-24 15:38:36', NULL, NULL, NULL);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admins`
--
ALTER TABLE `admins`
  ADD PRIMARY KEY (`admin_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `audit_logs`
--
ALTER TABLE `audit_logs`
  ADD PRIMARY KEY (`log_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `brands`
--
ALTER TABLE `brands`
  ADD PRIMARY KEY (`brand_id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `cart_items`
--
ALTER TABLE `cart_items`
  ADD PRIMARY KEY (`cart_item_id`),
  ADD KEY `customer_id` (`customer_id`),
  ADD KEY `variant_id` (`variant_id`);

--
-- Indexes for table `categories`
--
ALTER TABLE `categories`
  ADD PRIMARY KEY (`category_id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `customers`
--
ALTER TABLE `customers`
  ADD PRIMARY KEY (`customer_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `delivery_managers`
--
ALTER TABLE `delivery_managers`
  ADD PRIMARY KEY (`delivery_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `medicines`
--
ALTER TABLE `medicines`
  ADD PRIMARY KEY (`medicine_id`),
  ADD KEY `category_id` (`category_id`),
  ADD KEY `brand_id` (`brand_id`);

--
-- Indexes for table `medicine_variants`
--
ALTER TABLE `medicine_variants`
  ADD PRIMARY KEY (`variant_id`),
  ADD KEY `medicine_id` (`medicine_id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`notification_id`),
  ADD KEY `idx_user_read` (`user_id`,`is_read`),
  ADD KEY `idx_created` (`created_at`);

--
-- Indexes for table `orders`
--
ALTER TABLE `orders`
  ADD PRIMARY KEY (`order_id`),
  ADD KEY `customer_id` (`customer_id`),
  ADD KEY `delivery_id` (`delivery_id`);

--
-- Indexes for table `order_items`
--
ALTER TABLE `order_items`
  ADD PRIMARY KEY (`order_item_id`),
  ADD KEY `order_id` (`order_id`),
  ADD KEY `variant_id` (`variant_id`);

--
-- Indexes for table `pharmacists`
--
ALTER TABLE `pharmacists`
  ADD PRIMARY KEY (`pharmacist_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `prescriptions`
--
ALTER TABLE `prescriptions`
  ADD PRIMARY KEY (`prescription_id`),
  ADD KEY `customer_id` (`customer_id`),
  ADD KEY `order_id` (`order_id`);

--
-- Indexes for table `reviews`
--
ALTER TABLE `reviews`
  ADD PRIMARY KEY (`review_id`),
  ADD KEY `customer_id` (`customer_id`),
  ADD KEY `medicine_id` (`medicine_id`);

--
-- Indexes for table `saved_items`
--
ALTER TABLE `saved_items`
  ADD PRIMARY KEY (`saved_item_id`),
  ADD KEY `customer_id` (`customer_id`),
  ADD KEY `variant_id` (`variant_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admins`
--
ALTER TABLE `admins`
  MODIFY `admin_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `audit_logs`
--
ALTER TABLE `audit_logs`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `brands`
--
ALTER TABLE `brands`
  MODIFY `brand_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=37;

--
-- AUTO_INCREMENT for table `cart_items`
--
ALTER TABLE `cart_items`
  MODIFY `cart_item_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=87;

--
-- AUTO_INCREMENT for table `categories`
--
ALTER TABLE `categories`
  MODIFY `category_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `customers`
--
ALTER TABLE `customers`
  MODIFY `customer_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `delivery_managers`
--
ALTER TABLE `delivery_managers`
  MODIFY `delivery_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `medicines`
--
ALTER TABLE `medicines`
  MODIFY `medicine_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=96;

--
-- AUTO_INCREMENT for table `medicine_variants`
--
ALTER TABLE `medicine_variants`
  MODIFY `variant_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=96;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `notification_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=45;

--
-- AUTO_INCREMENT for table `orders`
--
ALTER TABLE `orders`
  MODIFY `order_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=39;

--
-- AUTO_INCREMENT for table `order_items`
--
ALTER TABLE `order_items`
  MODIFY `order_item_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=46;

--
-- AUTO_INCREMENT for table `pharmacists`
--
ALTER TABLE `pharmacists`
  MODIFY `pharmacist_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `prescriptions`
--
ALTER TABLE `prescriptions`
  MODIFY `prescription_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT for table `reviews`
--
ALTER TABLE `reviews`
  MODIFY `review_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `saved_items`
--
ALTER TABLE `saved_items`
  MODIFY `saved_item_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `admins`
--
ALTER TABLE `admins`
  ADD CONSTRAINT `admins_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `audit_logs`
--
ALTER TABLE `audit_logs`
  ADD CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `cart_items`
--
ALTER TABLE `cart_items`
  ADD CONSTRAINT `cart_items_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `cart_items_ibfk_2` FOREIGN KEY (`variant_id`) REFERENCES `medicine_variants` (`variant_id`) ON DELETE CASCADE;

--
-- Constraints for table `customers`
--
ALTER TABLE `customers`
  ADD CONSTRAINT `customers_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `delivery_managers`
--
ALTER TABLE `delivery_managers`
  ADD CONSTRAINT `delivery_managers_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `medicines`
--
ALTER TABLE `medicines`
  ADD CONSTRAINT `medicines_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`),
  ADD CONSTRAINT `medicines_ibfk_2` FOREIGN KEY (`brand_id`) REFERENCES `brands` (`brand_id`);

--
-- Constraints for table `medicine_variants`
--
ALTER TABLE `medicine_variants`
  ADD CONSTRAINT `medicine_variants_ibfk_1` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`medicine_id`) ON DELETE CASCADE;

--
-- Constraints for table `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `orders`
--
ALTER TABLE `orders`
  ADD CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`),
  ADD CONSTRAINT `orders_ibfk_2` FOREIGN KEY (`delivery_id`) REFERENCES `delivery_managers` (`delivery_id`);

--
-- Constraints for table `order_items`
--
ALTER TABLE `order_items`
  ADD CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`variant_id`) REFERENCES `medicine_variants` (`variant_id`);

--
-- Constraints for table `pharmacists`
--
ALTER TABLE `pharmacists`
  ADD CONSTRAINT `pharmacists_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `prescriptions`
--
ALTER TABLE `prescriptions`
  ADD CONSTRAINT `prescriptions_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `prescriptions_ibfk_2` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`);

--
-- Constraints for table `reviews`
--
ALTER TABLE `reviews`
  ADD CONSTRAINT `reviews_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `reviews_ibfk_2` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`medicine_id`) ON DELETE CASCADE;

--
-- Constraints for table `saved_items`
--
ALTER TABLE `saved_items`
  ADD CONSTRAINT `saved_items_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `saved_items_ibfk_2` FOREIGN KEY (`variant_id`) REFERENCES `medicine_variants` (`variant_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
