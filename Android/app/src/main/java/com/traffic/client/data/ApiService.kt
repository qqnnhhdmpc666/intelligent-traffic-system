package com.traffic.client.data

import retrofit2.Response
import retrofit2.http.*

/**
 * 交通调度系统API接口
 */
interface ApiService {
    
    /**
     * 获取系统信息
     */
    @GET("/")
    suspend fun getSystemInfo(): Response<SystemInfoResponse>
    
    /**
     * 健康检查
     */
    @GET("/health")
    suspend fun healthCheck(): Response<HealthResponse>
    
    /**
     * 同步路径规划
     */
    @POST("/api/request_path")
    suspend fun requestPath(@Body request: PathRequest): Response<PathResponse>
    
    /**
     * 异步路径规划
     */
    @POST("/api/request_path_async")
    suspend fun requestPathAsync(@Body request: PathRequest): Response<AsyncTaskResponse>
    
    /**
     * 查询异步任务状态
     */
    @GET("/api/task/{taskId}")
    suspend fun getTaskStatus(@Path("taskId") taskId: String): Response<TaskStatusResponse>
    
    /**
     * 获取系统统计
     */
    @GET("/api/system_stats")
    suspend fun getSystemStats(): Response<SystemStatsResponse>
    
    /**
     * 获取节点列表
     */
    @GET("/api/nodes")
    suspend fun getNodes(): Response<NodesResponse>
    
    /**
     * 获取道路列表
     */
    @GET("/api/roads")
    suspend fun getRoads(): Response<RoadsResponse>
    
    /**
     * 更新交通数据
     */
    @POST("/api/traffic_update")
    suspend fun updateTrafficData(@Body request: TrafficUpdateRequest): Response<TrafficUpdateResponse>
}

