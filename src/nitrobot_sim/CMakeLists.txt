cmake_minimum_required(VERSION 3.8)
project(nitrobot_sim)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

configure_file(
  "${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/extend_turtlebot3_ws.sh.in"
  "${CMAKE_CURRENT_BINARY_DIR}/env-hooks/extend_turtlebot3_ws.sh"
  @ONLY
)
ament_environment_hooks(
  "${CMAKE_CURRENT_BINARY_DIR}/env-hooks/extend_turtlebot3_ws.sh"
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

install(
  DIRECTORY launch worlds maps config rviz
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
  scripts/sim_teleop.sh
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
