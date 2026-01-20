package com.traffic.client

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.traffic.client.databinding.ActivityMainBinding
import com.traffic.client.ui.fragments.HomeFragment
import com.traffic.client.ui.fragments.MonitorFragment
import com.traffic.client.ui.fragments.PathPlanningFragment
import com.traffic.client.ui.fragments.SettingsFragment

/**
 * 主Activity
 * 负责管理底部导航和Fragment切换
 */
class MainActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityMainBinding
    
    // Fragment实例
    private val homeFragment = HomeFragment()
    private val pathPlanningFragment = PathPlanningFragment()
    private val monitorFragment = MonitorFragment()
    private val settingsFragment = SettingsFragment()
    
    // 当前显示的Fragment
    private var currentFragment: Fragment = homeFragment
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupToolbar()
        setupBottomNavigation()
        
        // 默认显示首页
        if (savedInstanceState == null) {
            showFragment(homeFragment, "首页")
        }
    }
    
    /**
     * 设置工具栏
     */
    private fun setupToolbar() {
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayShowTitleEnabled(true)
    }
    
    /**
     * 设置底部导航
     */
    private fun setupBottomNavigation() {
        binding.bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_home -> {
                    showFragment(homeFragment, "首页")
                    true
                }
                R.id.nav_path_planning -> {
                    showFragment(pathPlanningFragment, "路径规划")
                    true
                }
                R.id.nav_monitor -> {
                    showFragment(monitorFragment, "实时监控")
                    true
                }
                R.id.nav_settings -> {
                    showFragment(settingsFragment, "设置")
                    true
                }
                else -> false
            }
        }
        
        // 默认选中首页
        binding.bottomNavigation.selectedItemId = R.id.nav_home
    }
    
    /**
     * 显示指定Fragment
     */
    private fun showFragment(fragment: Fragment, title: String) {
        if (fragment == currentFragment) return
        
        val transaction = supportFragmentManager.beginTransaction()
        
        // 隐藏当前Fragment
        if (currentFragment.isAdded) {
            transaction.hide(currentFragment)
        }
        
        // 显示目标Fragment
        if (!fragment.isAdded) {
            transaction.add(R.id.nav_host_fragment, fragment)
        } else {
            transaction.show(fragment)
        }
        
        transaction.commit()
        currentFragment = fragment
        
        // 更新标题
        supportActionBar?.title = title
    }
    
    /**
     * 处理返回键
     */
    override fun onBackPressed() {
        // 如果不在首页，返回首页
        if (currentFragment != homeFragment) {
            binding.bottomNavigation.selectedItemId = R.id.nav_home
            return
        }
        
        // 在首页则退出应用
        super.onBackPressed()
    }
}

