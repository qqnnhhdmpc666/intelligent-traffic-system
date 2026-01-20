package com.traffic.client.ui.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import com.traffic.client.databinding.FragmentMonitorBinding

/**
 * 监控Fragment
 * 显示系统监控信息
 */
class MonitorFragment : Fragment() {
    
    private var _binding: FragmentMonitorBinding? = null
    private val binding get() = _binding!!
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentMonitorBinding.inflate(inflater, container, false)
        return binding.root
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupUI()
    }
    
    private fun setupUI() {
        // 简单的监控界面
        // 在实际项目中可以添加更多监控功能
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

