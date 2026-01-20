package com.traffic.client.ui.viewmodels

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.traffic.client.data.*
import com.traffic.client.repository.TrafficRepository
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * 路径规划ViewModel
 */
class PathPlanningViewModel : ViewModel() {
    
    private val repository = TrafficRepository.getInstance()
    
    // 节点列表
    private val _nodes = MutableLiveData<ApiResult<NodesResponse>>()
    val nodes: LiveData<ApiResult<NodesResponse>> = _nodes
    
    // 路径规划结果
    private val _pathResult = MutableLiveData<ApiResult<PathResponse>>()
    val pathResult: LiveData<ApiResult<PathResponse>> = _pathResult
    
    // 异步任务结果
    private val _asyncTaskResult = MutableLiveData<ApiResult<AsyncTaskResponse>>()
    val asyncTaskResult: LiveData<ApiResult<AsyncTaskResponse>> = _asyncTaskResult
    
    // 任务状态
    private val _taskStatus = MutableLiveData<ApiResult<TaskStatusResponse>>()
    val taskStatus: LiveData<ApiResult<TaskStatusResponse>> = _taskStatus
    
    /**
     * 加载节点列表
     */
    fun loadNodes() {
        viewModelScope.launch {
            _nodes.value = ApiResult.Loading("正在加载节点列表...")
            _nodes.value = repository.getNodes()
        }
    }
    
    /**
     * 同步路径规划
     */
    fun planRouteSync(request: PathRequest) {
        viewModelScope.launch {
            _pathResult.value = ApiResult.Loading("正在规划路径...")
            _pathResult.value = repository.requestPath(request)
        }
    }
    
    /**
     * 异步路径规划
     */
    fun planRouteAsync(request: PathRequest) {
        viewModelScope.launch {
            _asyncTaskResult.value = ApiResult.Loading("正在提交异步任务...")
            _asyncTaskResult.value = repository.requestPathAsync(request)
        }
    }
    
    /**
     * 轮询任务状态
     */
    fun pollTaskStatus(taskId: String) {
        viewModelScope.launch {
            var attempts = 0
            val maxAttempts = 30 // 最多轮询30次
            
            while (attempts < maxAttempts) {
                delay(2000) // 每2秒轮询一次
                
                val result = repository.getTaskStatus(taskId)
                _taskStatus.value = result
                
                if (result is ApiResult.Success) {
                    val status = result.data.status
                    if (status == "completed" || status == "failed") {
                        break // 任务完成或失败，停止轮询
                    }
                } else if (result is ApiResult.Error) {
                    break // 出错，停止轮询
                }
                
                attempts++
            }
            
            if (attempts >= maxAttempts) {
                _taskStatus.value = ApiResult.Error("任务状态查询超时")
            }
        }
    }
}

