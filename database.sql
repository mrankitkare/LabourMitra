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
  city VARCHAR(50) DEFAULT NULL,
  available TINYINT(1) DEFAULT 1,
  base_rate DECIMAL(10, 2) DEFAULT 0.00,
  min_rate DECIMAL(10, 2) DEFAULT 0.00,
  max_rate DECIMAL(10, 2) DEFAULT 0.00,
  current_rate DECIMAL(10, 2) DEFAULT 0.00,
  average_rating FLOAT DEFAULT 0.00,
  total_jobs INT DEFAULT 0,
  pending_rate_approval BOOLEAN DEFAULT 0,
  proposed_rate DECIMAL(10, 2) DEFAULT 0.00,
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
