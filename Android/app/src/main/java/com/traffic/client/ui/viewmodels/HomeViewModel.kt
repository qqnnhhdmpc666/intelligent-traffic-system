package com.traffic.client.ui.viewmodels

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.traffic.client.data.ApiResult
import com.traffic.client.data.SystemInfoResponse
import com.traffic.client.data.SystemStatsResponse
import com.traffic.client.repository.TrafficRepository
import kotlinx.coroutines.launch

/**
 * 首页ViewModel
 */
class HomeViewModel : ViewModel() {
    
    private val repository = TrafficRepository.getInstance()
    
    // 系统信息
    private val _systemInfo = MutableLiveData<ApiResult<SystemInfoResponse>>()
    val systemInfo: LiveData<ApiResult<SystemInfoResponse>> = _systemInfo
    
    // 系统统计
    private val _systemStats = MutableLiveData<ApiResult<SystemStatsResponse>>()
    val systemStats: LiveData<ApiResult<SystemStatsResponse>> = _systemStats
    
    /**
     * 加载系统信息
     */
    fun loadSystemInfo() {
        viewModelScope.launch {
            _systemInfo.value = ApiResult.Loading("正在连接服务器...")
            _systemInfo.value = repository.getSystemInfo()
        }
    }
    
    /**
     * 加载系统统计
     */
    fun loadSystemStats() {
        viewModelScope.launch {
            _systemStats.value = ApiResult.Loading("正在加载统计数据...")
            _systemStats.value = repository.getSystemStats()
        }
    }
    
    /**
     * 刷新所有数据
     */
    fun refreshAll() {
        loadSystemInfo()
        loadSystemStats()
    }
}

