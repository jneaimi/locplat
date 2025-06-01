# LocPlat Postman Testing Guide

## 📦 **Import the Collection**

1. **Download**: The collection is saved at `docs/LocPlat_Postman_Collection.json`
2. **Import**: Open Postman → Import → Upload the JSON file
3. **Setup**: Configure your API keys in the collection variables

## 🔑 **Configure API Keys**

Before testing, update these collection variables with your real API keys:

### **Required Variables:**
- `base_url`: `http://localhost:8000` (default)
- `openai_api_key`: Your OpenAI API key (sk-...)
- `anthropic_api_key`: Your Anthropic API key (sk-ant-...)
- `mistral_api_key`: Your Mistral AI API key
- `deepseek_api_key`: Your DeepSeek API key

### **How to Set Variables:**
1. Click on the collection name
2. Go to "Variables" tab
3. Update the "Current Value" for each API key
4. Save the collection

## 📋 **Collection Structure**

### **1. Health Check**
- ✅ **Service Health Status** - Verify all services are running

### **2. Provider Information**
- ✅ **Get All Providers and Models** - See available providers and their models
- ✅ **Get [Provider] Languages** - Check supported languages per provider

### **3. API Key Validation**
- ✅ **Validate [Provider] Key** - Test if your API keys are working

### **4. Language Direction**
- ✅ **Check Arabic Direction (RTL)** - Verify RTL detection
- ✅ **Check English Direction (LTR)** - Verify LTR detection
- ✅ **Check Bosnian Direction (LTR)** - Verify Bosnian direction

### **5. Single Translation Tests**
- ✅ **OpenAI: English to Arabic** - Test OpenAI with GPT-4o-mini
- ✅ **OpenAI: English to Bosnian** - Test OpenAI with Bosnian
- ✅ **Anthropic: English to Arabic** - Test Claude Haiku
- ✅ **Mistral: English to Arabic** - Test Mistral Small
- ✅ **DeepSeek: English to Bosnian** - Test DeepSeek Chat

### **6. Batch Translation Tests**
- ✅ **OpenAI: Batch English to Arabic** - Restaurant phrases batch
- ✅ **Anthropic: Batch English to Bosnian** - Politeness phrases batch

### **7. Model Comparison Tests**
- ✅ **OpenAI GPT-4o-mini (Low Cost)** - Same text, different models
- ✅ **OpenAI GPT-4o (High Quality)** - Compare quality vs cost
- ✅ **Anthropic Claude Haiku (Fast)** - Cross-provider comparison

### **8. Error Handling Tests**
- ✅ **Invalid Provider** - Test error responses
- ✅ **Invalid Language Code** - Test validation
- ✅ **Empty Text** - Test input validation
- ✅ **Invalid API Key** - Test authentication errors

### **9. Directus Integration Examples**
- ✅ **Blog Post Translation** - CMS content example
- ✅ **Product Description Batch** - E-commerce examples

## 🧪 **Recommended Testing Flow**

### **Step 1: Basic Verification**
1. Run "Service Health Status" - should return 200 OK
2. Run "Get All Providers and Models" - should show 4 providers
3. Run "Validate [Provider] Key" for your available providers

### **Step 2: Language Support**
1. Test "Get OpenAI Languages" - should show 20+ languages
2. Test language direction endpoints for ar, en, bs

### **Step 3: Translation Testing**
1. Start with **OpenAI English to Arabic** (if you have OpenAI key)
2. Try **batch translation** with restaurant phrases
3. Test **different providers** with the same text to compare

### **Step 4: Model Comparison**
1. Run the same text through different models
2. Compare quality scores and response times
3. Test cost vs quality trade-offs

### **Step 5: Error Handling**
1. Test invalid inputs to see proper error responses
2. Verify API validation is working correctly

## 🎯 **Expected Results**

### **Successful Translation Response:**
```json
{
  "translated_text": "مرحبا بالعالم",
  "provider_used": "openai",
  "model_used": "gpt-4o-mini", 
  "source_lang": "en",
  "target_lang": "ar",
  "quality_score": 0.92,
  "language_direction": "rtl",
  "metadata": {
    "provider_info": {...}
  }
}
```

### **Provider Information Response:**
```json
{
  "providers": ["openai", "anthropic", "mistral", "deepseek"],
  "models": {
    "openai": {
      "models": {
        "gpt-4o-mini": {"cost": "low", "quality": "high", "speed": "fast"}
      }
    }
  }
}
```

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **"Service Unavailable"** 
   - Check if Docker containers are running: `docker-compose ps`
   - Restart if needed: `docker-compose restart`

2. **"Invalid API Key"**
   - Verify your API key is correct in collection variables
   - Test key validation endpoints first

3. **"Provider not found"**
   - Check provider name spelling (lowercase: openai, anthropic, etc.)
   - Verify provider is in supported list

4. **"Language not supported"**
   - Check supported languages for that provider first
   - Use 2-letter language codes (en, ar, bs)

## 💡 **Tips for Testing**

- **Start Small**: Test single translations before batch operations
- **Compare Providers**: Use the same text across different providers
- **Test Edge Cases**: Empty text, invalid inputs, long text
- **Monitor Quality**: Check quality_score in responses
- **Cost Optimization**: Test cheaper models first, upgrade if needed

This collection provides comprehensive testing for all LocPlat features! 🚀
