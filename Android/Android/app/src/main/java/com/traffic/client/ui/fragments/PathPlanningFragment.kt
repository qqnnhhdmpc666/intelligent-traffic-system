package com.traffic.client.ui.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import com.traffic.client.R
import com.traffic.client.data.ApiResult
import com.traffic.client.data.PathRequest
import com.traffic.client.data.VehicleType
import com.traffic.client.databinding.FragmentPathPlanningBinding
import com.traffic.client.ui.viewmodels.PathPlanningViewModel
import kotlinx.coroutines.launch
import java.util.*

/**
 * 路径规划Fragment
 */
class PathPlanningFragment : Fragment() {
    
    private var _binding: FragmentPathPlanningBinding? = null
    private val binding get() = _binding!!
    
    private lateinit var viewModel: PathPlanningViewModel
    
    // 节点列表
    private val nodesList = mutableListOf<String>()
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentPathPlanningBinding.inflate(inflater, container, false)
        return binding.root
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        viewModel = ViewModelProvider(this)[PathPlanningViewModel::class.java]
        
        setupUI()
        observeViewModel()
        loadNodes()
    }
    
    /**
     * 设置UI
     */
    private fun setupUI() {
        // 设置车辆类型下拉菜单
        val vehicleTypes = VehicleType.values().map { it.displayName }
        val vehicleTypeAdapter = ArrayAdapter(
            requireContext(),
            android.R.layout.simple_dropdown_item_1line,
            vehicleTypes
        )
        binding.spinnerVehicleType.setAdapter(vehicleTypeAdapter)
        
        // 生成车辆ID按钮
        binding.btnGenerateId.setOnClickListener {
            generateVehicleId()
        }
        
        // 同步规划按钮
        binding.btnPlanSync.setOnClickListener {
            planRouteSync()
        }
        
        // 异步规划按钮
        binding.btnPlanAsync.setOnClickListener {
            planRouteAsync()
        }
        
        // 清除结果按钮
        binding.btnClearResult.setOnClickListener {
            clearResult()
        }
        
        // 默认生成一个车辆ID
        generateVehicleId()
    }
    
    /**
     * 观察ViewModel数据变化
     */
    private fun observeViewModel() {
        // 观察节点列表
        viewModel.nodes.observe(viewLifecycleOwner) { result ->
            when (result) {
                is ApiResult.Success -> {
                    nodesList.clear()
                    nodesList.addAll(result.data.nodes)
                    setupNodeSpinners()
                }
                is ApiResult.Error -> {
                    // 使用默认节点列表
                    setupDefaultNodes()
                    Toast.makeText(context, "获取节点列表失败，使用默认列表", Toast.LENGTH_SHORT).show()
                }
                else -> {
                    // Loading状态
                }
            }
        }
        
        // 观察路径规划结果
        viewModel.pathResult.observe(viewLifecycleOwner) { result ->
            when (result) {
                is ApiResult.Loading -> {
                    showResult("正在规划路径...")
                    setButtonsEnabled(false)
                }
                is ApiResult.Success -> {
                    val path = result.data
                    val resultText = buildString {
                        appendLine("路径规划成功！")
                        appendLine("路径: ${path.path.joinToString(" -> ")}")
                        appendLine("权重: ${String.format("%.2f", path.weight)}")
                        appendLine("处理时间: ${String.format("%.3f", path.processingTime)}秒")
                        appendLine("消息: ${path.message}")
                    }
                    showResult(resultText)
                    setButtonsEnabled(true)
                }
                is ApiResult.Error -> {
                    showResult("路径规划失败: ${result.message}")
                    setButtonsEnabled(true)
                }
            }
        }
        
        // 观察异步任务结果
        viewModel.asyncTaskResult.observe(viewLifecycleOwner) { result ->
            when (result) {
                is ApiResult.Loading -> {
                    showResult("正在提交异步任务...")
                    setButtonsEnabled(false)
                }
                is ApiResult.Success -> {
                    val task = result.data
                    showResult("异步任务已提交\n任务ID: ${task.taskId}\n状态: ${task.status}")
                    setButtonsEnabled(true)
                    
                    // 开始轮询任务状态
                    viewModel.pollTaskStatus(task.taskId)
                }
                is ApiResult.Error -> {
                    showResult("异步任务提交失败: ${result.message}")
                    setButtonsEnabled(true)
                }
            }
        }
        
        // 观察任务状态
        viewModel.taskStatus.observe(viewLifecycleOwner) { result ->
            when (result) {
                is ApiResult.Success -> {
                    val status = result.data
                    val resultText = buildString {
                        appendLine("任务状态更新")
                        appendLine("任务ID: ${status.taskId}")
                        appendLine("状态: ${status.status}")
                        
                        if (status.result != null) {
                            appendLine("\n路径规划结果:")
                            appendLine("路径: ${status.result.path.joinToString(" -> ")}")
                            appendLine("权重: ${String.format("%.2f", status.result.weight)}")
                            appendLine("处理时间: ${String.format("%.3f", status.result.processingTime)}秒")
                        }
                        
                        if (status.error != null) {
                            appendLine("错误: ${status.error}")
                        }
                        
                        appendLine("创建时间: ${status.createdAt}")
                        if (status.completedAt != null) {
                            appendLine("完成时间: ${status.completedAt}")
                        }
                    }
                    showResult(resultText)
                }
                is ApiResult.Error -> {
                    showResult("查询任务状态失败: ${result.message}")
                }
                else -> {
                    // Loading状态
                }
            }
        }
    }
    
    /**
     * 加载节点列表
     */
    private fun loadNodes() {
        lifecycleScope.launch {
            viewModel.loadNodes()
        }
    }
    
    /**
     * 设置节点下拉菜单
     */
    private fun setupNodeSpinners() {
        val adapter = ArrayAdapter(
            requireContext(),
            android.R.layout.simple_dropdown_item_1line,
            nodesList
        )
        
        binding.spinnerStartNode.setAdapter(adapter)
        binding.spinnerEndNode.setAdapter(adapter)
        
        // 设置默认值
        if (nodesList.isNotEmpty()) {
            binding.spinnerStartNode.setText(nodesList[0], false)
            if (nodesList.size > 1) {
                binding.spinnerEndNode.setText(nodesList[nodesList.size - 1], false)
            }
        }
    }
    
    /**
     * 设置默认节点列表
     */
    private fun setupDefaultNodes() {
        nodesList.clear()
        // 生成5x5网格节点
        for (i in 0..4) {
            for (j in 0..4) {
                nodesList.add("${('A' + i)}${j + 1}")
            }
        }
        setupNodeSpinners()
    }
    
    /**
     * 生成车辆ID
     */
    private fun generateVehicleId() {
        val id = "VEH_${System.currentTimeMillis() % 100000}"
        binding.etVehicleId.setText(id)
    }
    
    /**
     * 同步路径规划
     */
    private fun planRouteSync() {
        val request = createPathRequest() ?: return
        
        lifecycleScope.launch {
            viewModel.planRouteSync(request)
        }
    }
    
    /**
     * 异步路径规划
     */
    private fun planRouteAsync() {
        val request = createPathRequest() ?: return
        
        lifecycleScope.launch {
            viewModel.planRouteAsync(request)
        }
    }
    
    /**
     * 创建路径请求
     */
    private fun createPathRequest(): PathRequest? {
        val vehicleId = binding.etVehicleId.text.toString().trim()
        val vehicleTypeText = binding.spinnerVehicleType.text.toString()
        val startNode = binding.spinnerStartNode.text.toString().trim()
        val endNode = binding.spinnerEndNode.text.toString().trim()
        
        // 验证输入
        if (vehicleId.isEmpty()) {
            Toast.makeText(context, "请输入车辆ID", Toast.LENGTH_SHORT).show()
            return null
        }
        
        if (startNode.isEmpty()) {
            Toast.makeText(context, "请选择起始节点", Toast.LENGTH_SHORT).show()
            return null
        }
        
        if (endNode.isEmpty()) {
            Toast.makeText(context, "请选择目标节点", Toast.LENGTH_SHORT).show()
            return null
        }
        
        if (startNode == endNode) {
            Toast.makeText(context, "起始节点和目标节点不能相同", Toast.LENGTH_SHORT).show()
            return null
        }
        
        // 获取车辆类型
        val vehicleType = VehicleType.values().find { it.displayName == vehicleTypeText }?.value ?: "normal"
        
        return PathRequest(
            vehicleId = vehicleId,
            vehicleType = vehicleType,
            startNode = startNode,
            endNode = endNode
        )
    }
    
    /**
     * 显示结果
     */
    private fun showResult(text: String) {
        binding.tvResult.text = text
        binding.cardResult.visibility = View.VISIBLE
    }
    
    /**
     * 清除结果
     */
    private fun clearResult() {
        binding.cardResult.visibility = View.GONE
        binding.tvResult.text = ""
    }
    
    /**
     * 设置按钮启用状态
     */
    private fun setButtonsEnabled(enabled: Boolean) {
        binding.btnPlanSync.isEnabled = enabled
        binding.btnPlanAsync.isEnabled = enabled
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

