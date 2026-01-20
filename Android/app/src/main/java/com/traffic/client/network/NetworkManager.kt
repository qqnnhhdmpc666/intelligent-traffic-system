package com.traffic.client.network

import com.google.gson.GsonBuilder
import com.traffic.client.data.ApiService
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * 网络管理器
 * 负责创建和配置Retrofit实例
 */
object NetworkManager {
    
    // 服务器配置
    private const val BASE_URL = "http://120.53.28.58:3389/"
    private const val CONNECT_TIMEOUT = 30L
    private const val READ_TIMEOUT = 30L
    private const val WRITE_TIMEOUT = 30L
    
    // Gson配置
    private val gson = GsonBuilder()
        .setLenient()
        .create()
    
    // OkHttp客户端
    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(CONNECT_TIMEOUT, TimeUnit.SECONDS)
        .readTimeout(READ_TIMEOUT, TimeUnit.SECONDS)
        .writeTimeout(WRITE_TIMEOUT, TimeUnit.SECONDS)
        .addInterceptor(createLoggingInterceptor())
        .addInterceptor(createHeaderInterceptor())
        .retryOnConnectionFailure(true)
        .build()
    
    // Retrofit实例
    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create(gson))
        .build()
    
    // API服务实例
    val apiService: ApiService = retrofit.create(ApiService::class.java)
    
    /**
     * 创建日志拦截器
     */
    private fun createLoggingInterceptor(): HttpLoggingInterceptor {
        return HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
    }
    
    /**
     * 创建请求头拦截器
     */
    private fun createHeaderInterceptor() = okhttp3.Interceptor { chain ->
        val originalRequest = chain.request()
        val requestBuilder = originalRequest.newBuilder()
            .header("Content-Type", "application/json")
            .header("Accept", "application/json")
            .header("User-Agent", "TrafficClient-Android/1.0")
        
        chain.proceed(requestBuilder.build())
    }
    
    /**
     * 获取网络配置信息
     */
    fun getNetworkConfig(): NetworkConfig {
        return NetworkConfig(
            baseUrl = BASE_URL,
            connectTimeout = CONNECT_TIMEOUT,
            readTimeout = READ_TIMEOUT,
            writeTimeout = WRITE_TIMEOUT
        )
    }
}

/**
 * 网络配置数据类
 */
data class NetworkConfig(
    val baseUrl: String,
    val connectTimeout: Long,
    val readTimeout: Long,
    val writeTimeout: Long
)

