cmake_minimum_required(VERSION 3.8)
project(ros_car_teleop)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(rclcpp REQUIRED)

# Install Python executables
install(PROGRAMS
  scripts/teleop_node.py
  scripts/keyboard_controls.py
  scripts/safety_watchdog.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install resource directories
install(DIRECTORY
  launch
  rviz
  models
  DESTINATION share/${PROJECT_NAME}
)

ament_package()