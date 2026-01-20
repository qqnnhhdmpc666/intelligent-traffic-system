package com.traffic.client.ui.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.traffic.client.R
import com.traffic.client.data.ApiResult
import com.traffic.client.databinding.FragmentHomeBinding
import com.traffic.client.ui.viewmodels.HomeViewModel
import kotlinx.coroutines.launch

/**
 * 首页Fragment
 * 显示系统状态和快速操作
 */
class HomeFragment : Fragment() {
    
    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!
    
    private lateinit var viewModel: HomeViewModel
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        viewModel = ViewModelProvider(this)[HomeViewModel::class.java]
        
        setupUI()
        observeViewModel()
        loadData()
    }
    
    /**
     * 设置UI
     */
    private fun setupUI() {
        // 快速操作按钮
        binding.btnPlanRoute.setOnClickListener {
            navigateToPathPlanning()
        }
        
        binding.btnMonitorTraffic.setOnClickListener {
            navigateToMonitor()
        }
    }
    
    /**
     * 观察ViewModel数据变化
     */
    private fun observeViewModel() {
        // 观察系统信息
        viewModel.systemInfo.observe(viewLifecycleOwner) { result ->
            when (result) {
                is ApiResult.Loading -> {
                    updateConnectionStatus(false, "连接中...")
                }
                is ApiResult.Success -> {
                    updateConnectionStatus(true, "服务器已连接")
                }
                is ApiResult.Error -> {
                    updateConnectionStatus(false, "连接失败: ${result.message}")
                }
            }
        }
        
        // 观察系统统计
        viewModel.systemStats.observe(viewLifecycleOwner) { result ->
            when (result) {
                is ApiResult.Success -> {
                    val stats = result.data
                    binding.tvNodesCount.text = stats.totalNodes.toString()
                    binding.tvRoadsCount.text = stats.totalRoads.toString()
                    binding.tvTrafficFlow.text = stats.totalFlow.toString()
                }
                is ApiResult.Error -> {
                    // 使用默认值
                    binding.tvNodesCount.text = "25"
                    binding.tvRoadsCount.text = "80"
                    binding.tvTrafficFlow.text = "0"
                }
                else -> {
                    // Loading状态保持当前值
                }
            }
        }
    }
    
    /**
     * 加载数据
     */
    private fun loadData() {
        lifecycleScope.launch {
            viewModel.loadSystemInfo()
            viewModel.loadSystemStats()
        }
    }
    
    /**
     * 更新连接状态
     */
    private fun updateConnectionStatus(isConnected: Boolean, message: String) {
        binding.tvConnectionStatus.text = message
        
        val colorRes = if (isConnected) R.color.success_green else R.color.error_red
        binding.statusIndicator.backgroundTintList = 
            requireContext().getColorStateList(colorRes)
    }
    
    /**
     * 导航到路径规划页面
     */
    private fun navigateToPathPlanning() {
        val bottomNav = activity?.findViewById<BottomNavigationView>(R.id.bottom_navigation)
        bottomNav?.selectedItemId = R.id.nav_path_planning
    }
    
    /**
     * 导航到监控页面
     */
    private fun navigateToMonitor() {
        val bottomNav = activity?.findViewById<BottomNavigationView>(R.id.bottom_navigation)
        bottomNav?.selectedItemId = R.id.nav_monitor
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

