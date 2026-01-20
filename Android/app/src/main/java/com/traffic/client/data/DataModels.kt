package com.traffic.client.data

import com.google.gson.annotations.SerializedName

/**
 * 系统信息响应
 */
data class SystemInfoResponse(
    val message: String,
    val version: String,
    val status: String
)

/**
 * 健康检查响应
 */
data class HealthResponse(
    val status: String,
    val timestamp: String,
    val uptime: Double
)

/**
 * 路径请求
 */
data class PathRequest(
    @SerializedName("vehicle_id") val vehicleId: String,
    @SerializedName("vehicle_type") val vehicleType: String,
    @SerializedName("start_node") val startNode: String,
    @SerializedName("end_node") val endNode: String
)

/**
 * 路径响应
 */
data class PathResponse(
    val path: List<String>,
    val weight: Double,
    @SerializedName("processing_time") val processingTime: Double,
    val message: String
)

/**
 * 异步任务响应
 */
data class AsyncTaskResponse(
    @SerializedName("task_id") val taskId: String,
    val status: String,
    val message: String
)

/**
 * 任务状态响应
 */
data class TaskStatusResponse(
    @SerializedName("task_id") val taskId: String,
    val status: String,
    val result: PathResponse?,
    val error: String?,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("completed_at") val completedAt: String?
)

/**
 * 系统统计响应
 */
data class SystemStatsResponse(
    @SerializedName("total_nodes") val totalNodes: Int,
    @SerializedName("total_roads") val totalRoads: Int,
    @SerializedName("total_capacity") val totalCapacity: Int,
    @SerializedName("total_flow") val totalFlow: Int,
    @SerializedName("congested_roads") val congestedRoads: Int,
    @SerializedName("average_load_factor") val averageLoadFactor: Double,
    @SerializedName("thread_pool_stats") val threadPoolStats: ThreadPoolStats,
    @SerializedName("log_stats") val logStats: LogStats
)

/**
 * 线程池统计
 */
data class ThreadPoolStats(
    @SerializedName("max_workers") val maxWorkers: Int,
    @SerializedName("running_tasks") val runningTasks: Int,
    @SerializedName("pending_tasks") val pendingTasks: Int,
    @SerializedName("total_submitted") val totalSubmitted: Int,
    @SerializedName("total_completed") val totalCompleted: Int,
    @SerializedName("total_failed") val totalFailed: Int,
    @SerializedName("total_tasks") val totalTasks: Int,
    @SerializedName("queue_size") val queueSize: Int
)

/**
 * 日志统计
 */
data class LogStats(
    @SerializedName("log_dir") val logDir: String,
    @SerializedName("total_files") val totalFiles: Int,
    @SerializedName("total_size") val totalSize: Long,
    val files: List<LogFile>
)

/**
 * 日志文件
 */
data class LogFile(
    val name: String,
    val size: Long,
    @SerializedName("modified_time") val modifiedTime: String
)

/**
 * 节点响应
 */
data class NodesResponse(
    val nodes: List<String>
)

/**
 * 道路响应
 */
data class RoadsResponse(
    val roads: List<Road>
)

/**
 * 道路信息
 */
data class Road(
    val from: String,
    val to: String,
    val weight: Double,
    val capacity: Int,
    val flow: Int,
    @SerializedName("load_factor") val loadFactor: Double
)

/**
 * 交通更新请求
 */
data class TrafficUpdateRequest(
    @SerializedName("intersection_id") val intersectionId: String,
    @SerializedName("traffic_data") val trafficData: Map<String, Int>
)

/**
 * 交通更新响应
 */
data class TrafficUpdateResponse(
    val status: String,
    val message: String,
    @SerializedName("updated_roads") val updatedRoads: Int
)

/**
 * API响应包装类
 */
sealed class ApiResult<T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class Error<T>(val message: String, val code: Int? = null) : ApiResult<T>()
    data class Loading<T>(val message: String = "加载中...") : ApiResult<T>()
}

/**
 * 车辆类型枚举
 */
enum class VehicleType(val value: String, val displayName: String) {
    NORMAL("normal", "普通车辆"),
    EMERGENCY("emergency", "紧急车辆")
}

/**
 * 任务状态枚举
 */
enum class TaskStatus(val value: String, val displayName: String) {
    PENDING("pending", "等待中"),
    RUNNING("running", "运行中"),
    COMPLETED("completed", "已完成"),
    FAILED("failed", "失败")
}

