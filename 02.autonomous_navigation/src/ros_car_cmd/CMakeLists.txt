cmake_minimum_required(VERSION 3.8)
project(ros_car_cmd)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(rclcpp REQUIRED)

# Install Python executables
install(PROGRAMS
  scripts/waypoint_manager.py
  scripts/waypoint_navigator.py
  scripts/waypoint_visualizer.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install resource directories
install(DIRECTORY
  launch
  config
  rviz
  DESTINATION share/${PROJECT_NAME}
)

ament_package()