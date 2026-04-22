CREATE DATABASE IF NOT EXISTS labourmitra;
USE labourmitra;

-- -----------------------------------------------------
-- Table `users`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  mobile VARCHAR(10) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  role ENUM('labour', 'customer') NOT NULL,
  skill VARCHAR(50) DEFAULT NULL,
  category VARCHAR(50) DEFAULT NULL,
  city VARCHAR(50) DEFAULT NULL,
  area VARCHAR(100) DEFAULT NULL,
  available TINYINT(1) DEFAULT 1,
  base_rate DECIMAL(10, 2) DEFAULT 0.00,
  min_rate DECIMAL(10, 2) DEFAULT 0.00,
  max_rate DECIMAL(10, 2) DEFAULT 0.00,
  current_rate DECIMAL(10, 2) DEFAULT 0.00,
  average_rating FLOAT DEFAULT 0.00,
  total_jobs INT DEFAULT 0,
  total_reviews INT DEFAULT 0,
  wallet_balance DECIMAL(10, 2) DEFAULT 0.00,
  pending_rate_approval BOOLEAN DEFAULT 0,
  proposed_rate DECIMAL(10, 2) DEFAULT 0.00,
  aadhaar_number VARCHAR(20) DEFAULT NULL,
  id_proof_type VARCHAR(50) DEFAULT NULL,
  profile_photo VARCHAR(255) DEFAULT NULL,
  id_proof_image VARCHAR(255) DEFAULT NULL,
  aadhaar_front_image VARCHAR(255) DEFAULT NULL,
  aadhaar_back_image VARCHAR(255) DEFAULT NULL,
  address_proof_document VARCHAR(255) DEFAULT NULL,
  verification_status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
  is_blocked BOOLEAN DEFAULT 0,
  otp_code VARCHAR(6) DEFAULT NULL,
  otp_expiry TIMESTAMP DEFAULT NULL,
  failed_otp_attempts INT DEFAULT 0,
  latitude DECIMAL(10, 8) DEFAULT NULL,
  longitude DECIMAL(11, 8) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------
-- Table `bookings`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS bookings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  labour_id INT NOT NULL,
  status ENUM('Pending', 'Accepted', 'Rejected', 'Completed') DEFAULT 'Pending',
  amount DECIMAL(10, 2) DEFAULT 0.00,
  commission DECIMAL(10, 2) DEFAULT 0.00,
  payment_status ENUM('Pending', 'Paid') DEFAULT 'Pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (labour_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Table `reviews`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
  id INT AUTO_INCREMENT PRIMARY KEY,
  booking_id INT NOT NULL,
  customer_id INT NOT NULL,
  labour_id INT NOT NULL,
  rating INT CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (labour_id) REFERENCES users(id) ON DELETE CASCADE
);
