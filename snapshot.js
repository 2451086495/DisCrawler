var page = require('webpage').create();  
system = require('system');  
//var url = 'http://yule.club.sohu.com/gifttrade/thread/2m2efbrpfui';  
var address;  
if(system.args.length != 3){  
    phantom.exit();  
}else{  
    adress = system.args[1];  
    page.open(adress, function (status){  
    if (status != "success"){  
        console.log('FAIL to load the address');  
        phantom.exit();  
    }  
          
    page.evaluate(function(){  
        //�˺�����Ŀ��ҳ��ִ�еģ������Ļ����Ǳ�phantomjs�����Բ����õ����js����������         
        window.scrollTo(0,10000);//�������ײ�  
        //window.document.body.scrollTop = document.body.scrollHeight;  
          
        window.setTimeout(function(){  
            var plist = document.querySelectorAll("a");  
            var len = plist.length;  
            while(len)  
            {  
                len--;  
                var el = plist[len];  
                el.style.border = "1px solid red";  
            }  
        },50);  
    });  
      
    window.setTimeout(function (){  
            //�ڱ������ɽ�ͼ  
        page.render(system.args[2]);         
        phantom.exit();  
    }, 200);      
    });  
} 