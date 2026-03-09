CREATE DATABASE  IF NOT EXISTS `phc` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `phc`;
-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: phc_front
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `account`
--

DROP TABLE IF EXISTS `account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `account` (
  `id_account` int NOT NULL AUTO_INCREMENT,
  `status` tinyint NOT NULL,
  `user` varchar(45) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `password` varchar(100) DEFAULT NULL,
  `subscription` varchar(45) NOT NULL,
  `google_id` varchar(255) DEFAULT NULL,
  `facebook_id` varchar(255) DEFAULT NULL,
  `subscription_expires_at` datetime DEFAULT NULL,
  `observations_admin` text,
  PRIMARY KEY (`id_account`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=88 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `address`
--

DROP TABLE IF EXISTS `address`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `address` (
  `id_address` int NOT NULL AUTO_INCREMENT,
  `street` varchar(100) DEFAULT NULL,
  `city` varchar(45) DEFAULT NULL,
  `state` varchar(45) DEFAULT NULL,
  `zip_code` varchar(10) DEFAULT NULL,
  `country` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id_address`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `application`
--

DROP TABLE IF EXISTS `application`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `application` (
  `id_application` int NOT NULL AUTO_INCREMENT,
  `candidate_id` int NOT NULL,
  `job_id` int NOT NULL,
  `applied_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('applied','reviewed','accepted','rejected') DEFAULT 'applied',
  PRIMARY KEY (`id_application`),
  KEY `fk_application_candidate` (`candidate_id`),
  KEY `fk_application_job` (`job_id`),
  CONSTRAINT `fk_application_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `candidate` (`id_candidate`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_application_job` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`id_jobs`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `candidate`
--

DROP TABLE IF EXISTS `candidate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `candidate` (
  `id_candidate` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `first_name` varchar(45) NOT NULL,
  `last_name` varchar(45) NOT NULL,
  `phone_number` varchar(20) NOT NULL,
  `emergency_contact_name` varchar(100) DEFAULT NULL,
  `emergency_contact_phone` varchar(20) DEFAULT NULL,
  `address_id` int NOT NULL,
  `education_id` int NOT NULL,
  `desired_position` varchar(100) DEFAULT NULL,
  `years_experience` int DEFAULT NULL,
  `last_position` varchar(100) DEFAULT NULL,
  `last_company` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `job_type` varchar(45) DEFAULT NULL,
  `employment_type` varchar(45) DEFAULT NULL,
  `modality` varchar(45) DEFAULT NULL,
  `salary` varchar(75) DEFAULT NULL,
  `status` enum('active','inactive') DEFAULT 'active',
  `radius` int DEFAULT NULL,
  `adult` tinyint(1) NOT NULL DEFAULT '1',
  `work_permission` tinyint(1) NOT NULL DEFAULT '1',
  `web_link` varchar(100) DEFAULT NULL,
  `about` text,
  `photo` varchar(255) DEFAULT NULL,
  `cvu` varchar(255) DEFAULT NULL,
  `servsafe` varchar(25) NOT NULL DEFAULT 'na',
  `is_active` tinyint(1) NOT NULL DEFAULT '0',
  `profile_views` int unsigned NOT NULL DEFAULT '0',
  `cvu_downloads` int unsigned NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_candidate`),
  KEY `fk_candidate_account` (`account_id`),
  KEY `fk_candidate_address` (`address_id`),
  KEY `fk_candidate_education` (`education_id`),
  CONSTRAINT `fk_candidate_account` FOREIGN KEY (`account_id`) REFERENCES `account` (`id_account`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_candidate_address` FOREIGN KEY (`address_id`) REFERENCES `address` (`id_address`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_candidate_education` FOREIGN KEY (`education_id`) REFERENCES `education` (`id_education`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `candidate_has_schedule`
--

DROP TABLE IF EXISTS `candidate_has_schedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `candidate_has_schedule` (
  `candidate_id` int NOT NULL,
  `schedule_id` int NOT NULL,
  PRIMARY KEY (`candidate_id`,`schedule_id`),
  KEY `fk_candidate_schedule_schedule` (`schedule_id`),
  CONSTRAINT `fk_candidate_schedule_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `candidate` (`id_candidate`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_candidate_schedule_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `schedule` (`id_schedule`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `company`
--

DROP TABLE IF EXISTS `company`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `company` (
  `id_company` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `type_business` varchar(100) DEFAULT NULL,
  `account_id` int NOT NULL,
  `address_id` int NOT NULL,
  `primary_contact` varchar(45) NOT NULL,
  `title_pc` varchar(45) NOT NULL,
  `phone_number_pc` varchar(20) NOT NULL,
  `email_pc` varchar(100) NOT NULL,
  `secondary_contact` varchar(45) DEFAULT NULL,
  `title_sc` varchar(45) DEFAULT NULL,
  `phone_number_sc` varchar(20) DEFAULT NULL,
  `email_sc` varchar(100) DEFAULT NULL,
  `description` varchar(500) NOT NULL,
  `link` varchar(100) NOT NULL,
  `logo` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `cvu_downloads` int NOT NULL DEFAULT '0',
  `profile_views` int NOT NULL DEFAULT '0',
  `first_contact_applications` int NOT NULL DEFAULT '0',
  `first_contact_search` int NOT NULL DEFAULT '0',
  `subscription` varchar(50) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_company`),
  KEY `fk_company_account` (`account_id`),
  KEY `fk_company_address` (`address_id`),
  CONSTRAINT `fk_company_account` FOREIGN KEY (`account_id`) REFERENCES `account` (`id_account`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_company_address` FOREIGN KEY (`address_id`) REFERENCES `address` (`id_address`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `education`
--

DROP TABLE IF EXISTS `education`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `education` (
  `id_education` int NOT NULL AUTO_INCREMENT,
  `country` varchar(45) NOT NULL,
  `education` varchar(100) NOT NULL,
  `education_field` varchar(150) NOT NULL,
  `graduation_year` varchar(10) NOT NULL,
  `institute` varchar(100) NOT NULL,
  PRIMARY KEY (`id_education`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `job_applications`
--

DROP TABLE IF EXISTS `job_applications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `job_applications` (
  `id_job_application` int NOT NULL AUTO_INCREMENT,
  `id_jobs` int NOT NULL,
  `id_candidate` int NOT NULL,
  `status` enum('application_submitted','application_viewed','applied','review','accepted','rejected') COLLATE utf8mb4_unicode_ci DEFAULT 'application_submitted',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_job_application`),
  KEY `id_jobs` (`id_jobs`),
  KEY `id_candidate` (`id_candidate`),
  CONSTRAINT `job_applications_ibfk_1` FOREIGN KEY (`id_jobs`) REFERENCES `jobs` (`id_jobs`),
  CONSTRAINT `job_applications_ibfk_2` FOREIGN KEY (`id_candidate`) REFERENCES `candidate` (`id_candidate`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `jobs`
--

DROP TABLE IF EXISTS `jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jobs` (
  `id_jobs` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `title` varchar(100) NOT NULL,
  `location` varchar(100) NOT NULL,
  `salary` varchar(75) NOT NULL,
  `experience` varchar(250) DEFAULT NULL,
  `employment_type` varchar(45) NOT NULL,
  `modality` varchar(45) NOT NULL,
  `benefits` varchar(200) DEFAULT NULL,
  `description` text NOT NULL,
  `is_active` tinyint NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `auto_close` tinyint(1) DEFAULT '0',
  `other` varchar(400) DEFAULT NULL,
  `oportunity` varchar(400) DEFAULT NULL,
  `qualifications` text,
  `latitude` double DEFAULT NULL,
  `longitude` double DEFAULT NULL,
  `job_type` varchar(60) DEFAULT NULL,
  PRIMARY KEY (`id_jobs`),
  KEY `fk_jobs_company` (`company_id`),
  CONSTRAINT `fk_jobs_company` FOREIGN KEY (`company_id`) REFERENCES `company` (`id_company`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `message`
--

DROP TABLE IF EXISTS `message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `message` (
  `id_message` int NOT NULL AUTO_INCREMENT,
  `sender_account_id` int NOT NULL,
  `receiver_account_id` int NOT NULL,
  `message` text NOT NULL,
  `status` tinyint NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `conversation_id` int DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_message`),
  KEY `fk_message_sender` (`sender_account_id`),
  KEY `fk_message_receiver` (`receiver_account_id`),
  CONSTRAINT `fk_message_receiver` FOREIGN KEY (`receiver_account_id`) REFERENCES `account` (`id_account`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_message_sender` FOREIGN KEY (`sender_account_id`) REFERENCES `account` (`id_account`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=103 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `schedule`
--

DROP TABLE IF EXISTS `schedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `schedule` (
  `id_schedule` int NOT NULL AUTO_INCREMENT,
  `time_start` time NOT NULL,
  `time_finish` time NOT NULL,
  `day` varchar(3) DEFAULT NULL,
  `type` varchar(20) DEFAULT NULL,
  `date_start` date DEFAULT NULL,
  `date_end` date DEFAULT NULL,
  PRIMARY KEY (`id_schedule`)
) ENGINE=InnoDB AUTO_INCREMENT=370 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `schedule_has_jobs`
--

DROP TABLE IF EXISTS `schedule_has_jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `schedule_has_jobs` (
  `schedule_id` int NOT NULL,
  `jobs_id` int NOT NULL,
  PRIMARY KEY (`schedule_id`,`jobs_id`),
  KEY `fk_schedule_jobs_job` (`jobs_id`),
  CONSTRAINT `fk_schedule_jobs_job` FOREIGN KEY (`jobs_id`) REFERENCES `jobs` (`id_jobs`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_schedule_jobs_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `schedule` (`id_schedule`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `skills`
--

DROP TABLE IF EXISTS `skills`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `skills` (
  `id_skills` int NOT NULL AUTO_INCREMENT,
  `name` varchar(45) NOT NULL,
  PRIMARY KEY (`id_skills`)
) ENGINE=InnoDB AUTO_INCREMENT=58 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `skills_has_jobs`
--

DROP TABLE IF EXISTS `skills_has_jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `skills_has_jobs` (
  `skills_id` int NOT NULL,
  `jobs_id` int NOT NULL,
  PRIMARY KEY (`skills_id`,`jobs_id`),
  KEY `fk_skills_jobs_job` (`jobs_id`),
  CONSTRAINT `fk_skills_jobs_job` FOREIGN KEY (`jobs_id`) REFERENCES `jobs` (`id_jobs`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_skills_jobs_skill` FOREIGN KEY (`skills_id`) REFERENCES `skills` (`id_skills`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-27 16:55:52
