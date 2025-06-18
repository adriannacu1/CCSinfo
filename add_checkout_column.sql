-- Add check_out_time column to student_attendance table
ALTER TABLE `student_attendance` 
ADD COLUMN `check_out_time` DATETIME NULL DEFAULT NULL AFTER `check_in_time`;
