// Republishes /scan as /scan_slam with no-return beams (inf/NaN) set just under range_max.
// slam_toolbox (Karto) skips readings >= the sensor's range_max entirely, so with a 3.5 m
// lidar, open space beyond the lidar's reach is never marked free and the explorer keeps
// chasing frontiers that can't clear. With slam_toolbox's max_laser_range below range_max,
// these filled beams clear free space up to max_laser_range without marking an obstacle.
#include <cmath>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<rclcpp::Node>("scan_filler");
    auto pub = node->create_publisher<sensor_msgs::msg::LaserScan>("/scan_slam", rclcpp::SensorDataQoS());
    auto sub = node->create_subscription<sensor_msgs::msg::LaserScan>(
        "/scan", rclcpp::SensorDataQoS(), [pub](sensor_msgs::msg::LaserScan::UniquePtr msg) {
            const float fill = msg->range_max - 0.01f;
            for (auto& r : msg->ranges)
                if (!std::isfinite(r) || r >= msg->range_max) r = fill;
            pub->publish(std::move(msg));
        });
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
