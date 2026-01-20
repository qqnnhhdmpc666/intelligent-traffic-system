package com.traffic.client.repository

import com.traffic.client.data.*
import com.traffic.client.network.NetworkManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.Response

/**
 * 交通数据仓库
 * 负责数据的获取和缓存
 */
class TrafficRepository {
    
    private val apiService = NetworkManager.apiService
    
    /**
     * 获取系统信息
     */
    suspend fun getSystemInfo(): ApiResult<SystemInfoResponse> {
        return safeApiCall { apiService.getSystemInfo() }
    }
    
    /**
     * 健康检查
     */
    suspend fun healthCheck(): ApiResult<HealthResponse> {
        return safeApiCall { apiService.healthCheck() }
    }
    
    /**
     * 同步路径规划
     */
    suspend fun requestPath(request: PathRequest): ApiResult<PathResponse> {
        return safeApiCall { apiService.requestPath(request) }
    }
    
    /**
     * 异步路径规划
     */
    suspend fun requestPathAsync(request: PathRequest): ApiResult<AsyncTaskResponse> {
        return safeApiCall { apiService.requestPathAsync(request) }
    }
    
    /**
     * 查询异步任务状态
     */
    suspend fun getTaskStatus(taskId: String): ApiResult<TaskStatusResponse> {
        return safeApiCall { apiService.getTaskStatus(taskId) }
    }
    
    /**
     * 获取系统统计
     */
    suspend fun getSystemStats(): ApiResult<SystemStatsResponse> {
        return safeApiCall { apiService.getSystemStats() }
    }
    
    /**
     * 获取节点列表
     */
    suspend fun getNodes(): ApiResult<NodesResponse> {
        return safeApiCall { apiService.getNodes() }
    }
    
    /**
     * 获取道路列表
     */
    suspend fun getRoads(): ApiResult<RoadsResponse> {
        return safeApiCall { apiService.getRoads() }
    }
    
    /**
     * 更新交通数据
     */
    suspend fun updateTrafficData(request: TrafficUpdateRequest): ApiResult<TrafficUpdateResponse> {
        return safeApiCall { apiService.updateTrafficData(request) }
    }
    
    /**
     * 安全的API调用包装器
     */
    private suspend fun <T> safeApiCall(apiCall: suspend () -> Response<T>): ApiResult<T> {
        return withContext(Dispatchers.IO) {
            try {
                val response = apiCall()
                if (response.isSuccessful) {
                    response.body()?.let { body ->
                        ApiResult.Success(body)
                    } ?: ApiResult.Error("响应体为空")
                } else {
                    val errorMessage = when (response.code()) {
                        400 -> "请求参数错误"
                        401 -> "未授权访问"
                        403 -> "访问被禁止"
                        404 -> "请求的资源不存在"
                        500 -> "服务器内部错误"
                        502 -> "网关错误"
                        503 -> "服务不可用"
                        504 -> "网关超时"
                        else -> "未知错误 (${response.code()})"
                    }
                    ApiResult.Error(errorMessage, response.code())
                }
            } catch (e: java.net.SocketTimeoutException) {
                ApiResult.Error("请求超时，请检查网络连接")
            } catch (e: java.net.ConnectException) {
                ApiResult.Error("无法连接到服务器，请检查网络设置")
            } catch (e: java.net.UnknownHostException) {
                ApiResult.Error("无法解析服务器地址")
            } catch (e: Exception) {
                ApiResult.Error("网络请求失败: ${e.message}")
            }
        }
    }
    
    companion object {
        @Volatile
        private var INSTANCE: TrafficRepository? = null
        
        fun getInstance(): TrafficRepository {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: TrafficRepository().also { INSTANCE = it }
            }
        }
    }
}

