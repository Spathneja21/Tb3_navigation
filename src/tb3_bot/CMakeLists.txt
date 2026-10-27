cmake_minimum_required(VERSION 3.8)
project(tb3_bot)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2_ros REQUIRED)

# Frontier explorer: reads /scan, /odom, /map and the map->base_link TF, drives /cmd_vel.
add_executable(lidar_explorer src/lidar_explorer.cpp)
ament_target_dependencies(lidar_explorer rclcpp sensor_msgs geometry_msgs nav_msgs tf2_ros)
install(TARGETS lidar_explorer DESTINATION lib/${PROJECT_NAME})

# scan_filler: /scan -> /scan_slam with no-return beams filled, so SLAM clears open space
add_executable(scan_filler src/scan_filler.cpp)
ament_target_dependencies(scan_filler rclcpp sensor_msgs)
install(TARGETS scan_filler DESTINATION lib/${PROJECT_NAME})

# launch files, configs and maps are installed copies: rebuild after editing them
install(DIRECTORY launch config models maps DESTINATION share/${PROJECT_NAME})

ament_package()
