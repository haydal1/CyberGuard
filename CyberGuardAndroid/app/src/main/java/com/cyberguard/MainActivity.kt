package com.cyberguard

import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Switch
import android.widget.LinearLayout
import androidx.core.content.ContextCompat
import com.google.android.material.tabs.TabLayout
import android.Manifest
import android.content.pm.PackageManager
import androidx.core.app.ActivityCompat
import android.content.Intent
import android.provider.Settings
import android.net.Uri

class MainActivity : AppCompatActivity() {
    private lateinit var ussdChecker: USSDChecker
    private lateinit var smsChecker: SMSChecker
    private lateinit var checkButton: Button
    private lateinit var inputField: EditText
    private lateinit var resultText: TextView
    private lateinit var tabLayout: TabLayout
    private lateinit var autoSmsSwitch: Switch
    private lateinit var permissionLayout: LinearLayout
    
    // SMS Permissions
    private val smsPermissions = arrayOf(
        Manifest.permission.RECEIVE_SMS,
        Manifest.permission.READ_SMS
    )
    private val smsPermissionCode = 100
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Initialize security checkers
        ussdChecker = USSDChecker(this)
        smsChecker = SMSChecker(this)
        
        // Initialize UI components
        initializeViews()
        setupClickListeners()
        setupTabs()
        checkPermissions()
        
        // Show database stats in logs for debugging
        println("CyberGuard: ${ussdChecker.getDatabaseStats()}")
        println("CyberGuard: SMS fraud detection ready")
    }
    
    private fun initializeViews() {
        checkButton = findViewById(R.id.checkButton)
        inputField = findViewById(R.id.ussdInput)
        resultText = findViewById(R.id.resultText)
        tabLayout = findViewById(R.id.tabLayout)
        autoSmsSwitch = findViewById(R.id.autoSmsSwitch)
        permissionLayout = findViewById(R.id.permissionLayout)
        
        // Load auto-detection preference
        val prefs = getSharedPreferences("cyberguard_prefs", MODE_PRIVATE)
        autoSmsSwitch.isChecked = prefs.getBoolean("auto_sms_detection", true)
    }
    
    private fun setupTabs() {
        tabLayout.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab?) {
                when (tab?.position) {
                    0 -> { // USSD Tab
                        inputField.hint = "Enter USSD code (e.g., *901#)"
                        checkButton.text = "Check USSD Safety"
                        permissionLayout.visibility = LinearLayout.GONE
                    }
                    1 -> { // SMS Tab
                        inputField.hint = "Enter SMS message to check"
                        checkButton.text = "Check SMS Safety"
                        permissionLayout.visibility = LinearLayout.VISIBLE
                        checkPermissions()
                    }
                }
            }
            
            override fun onTabUnselected(tab: TabLayout.Tab?) {}
            override fun onTabReselected(tab: TabLayout.Tab?) {}
        })
    }
    
    private fun setupClickListeners() {
        checkButton.setOnClickListener {
            val input = inputField.text.toString().trim()
            when (tabLayout.selectedTabPosition) {
                0 -> checkUSSDCode(input)  // USSD check
                1 -> checkSMSText(input)   // SMS check
            }
        }
        
        autoSmsSwitch.setOnCheckedChangeListener { _, isChecked ->
            val prefs = getSharedPreferences("cyberguard_prefs", MODE_PRIVATE)
            prefs.edit().putBoolean("auto_sms_detection", isChecked).apply()
            
            if (isChecked) {
                checkPermissions()
            }
        }
        
        // Permission request button
        findViewById<Button>(R.id.permissionButton).setOnClickListener {
            requestSmsPermissions()
        }
        
        // Settings button for manual permission granting
        findViewById<Button>(R.id.settingsButton).setOnClickListener {
            val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                data = Uri.fromParts("package", packageName, null)
            }
            startActivity(intent)
        }
    }
    
    private fun checkUSSDCode(code: String) {
        if (code.isEmpty()) {
            showResult(SecurityResult(false, 0, "❌ Please enter a USSD code", "gray"))
            return
        }
        
        // Perform USSD security check
        val result = ussdChecker.checkCode(code)
        showResult(result)
    }
    
    private fun checkSMSText(message: String) {
        if (message.isEmpty()) {
            showResult(SecurityResult(false, 0, "❌ Please enter an SMS message", "gray"))
            return
        }
        
        // Perform SMS security check
        val result = smsChecker.checkSMS(message)
        showResult(result)
    }
    
    private fun showResult(result: SecurityResult) {
        resultText.text = result.message
        
        // Set background color based on safety level
        val color = when {
            result.isSafe -> R.color.safe_green
            result.confidence >= 80 -> R.color.danger_red
            else -> R.color.warning_orange
        }
        
        resultText.setBackgroundColor(ContextCompat.getColor(this, color))
        
        // Log the result for debugging
        println("CyberGuard Check: '${inputField.text}' -> ${result.message}")
    }
    
    private fun checkPermissions() {
        val hasPermissions = smsPermissions.all { permission ->
            ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED
        }
        
        if (hasPermissions) {
            permissionLayout.visibility = LinearLayout.GONE
            autoSmsSwitch.isEnabled = true
        } else {
            permissionLayout.visibility = LinearLayout.VISIBLE
            autoSmsSwitch.isEnabled = false
        }
    }
    
    private fun requestSmsPermissions() {
        ActivityCompat.requestPermissions(this, smsPermissions, smsPermissionCode)
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        
        if (requestCode == smsPermissionCode) {
            val allGranted = grantResults.all { it == PackageManager.PERMISSION_GRANTED }
            if (allGranted) {
                permissionLayout.visibility = LinearLayout.GONE
                autoSmsSwitch.isEnabled = true
                autoSmsSwitch.isChecked = true
            } else {
                // Permissions denied
                autoSmsSwitch.isChecked = false
            }
        }
    }
}
