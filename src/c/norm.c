//
//  main2.cpp
//  norm
//
//  Created by Ben Lin on 10/2/18.
//  Copyright © 2018 Ben Lin. All rights reserved.
//


#include <iterator>
#include <set>
#include <regex>
#include <iostream>
#include <string>         // std::string, std::u32string
#include <locale>         // std::wstring_convert
#include <codecvt>        // std::codecvt_utf8
using namespace std;



//https://www.oschina.net/code/snippet_871213_45571
//全角字符的定义为 unicode编码从0xFF01~0xFF5E 对应的半角字符为 半角字符unicode编码从0x21~0x7E
string Half(string input){
    std::string temp;
    for (size_t i = 0; i < input.size(); i++) {
        if (((input[i] & 0xF0) ^ 0xE0) == 0) {
            int old_char = (input[i] & 0xF) << 12 | ((input[i + 1] & 0x3F) << 6 | (input[i + 2] & 0x3F));
            if (old_char == 0x3000) { // blank
                char new_char = 0x20;
                temp += new_char;
            } else if (old_char >= 0xFF01 && old_char <= 0xFF5E) { // full char
                char new_char = old_char - 0xFEE0;
                temp += new_char;
            } else { // other 3 bytes char
                temp += input[i];
                temp += input[i + 1];
                temp += input[i + 2];
            }
            i = i + 2;
        } else {
            temp += input[i];
        }
    }
    return temp;
}


//unicode emocon: U+1F600..U+1F64F
string ReplaceSmileyAndSign(string input){
    static const regex regex_dongdongsmiley("#E-s\\d+");
    string temp1 = regex_replace( input, regex_dongdongsmiley, " ");

    static const wstring wsigns = L"！？｡＂＃＄％＆＇（）＊＋，／；＜＝＞＠。［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…﹏";

    std::wstring_convert<std::codecvt_utf8<wchar_t>> cv;
    wstring winput = cv.from_bytes(temp1);
    wstring wtemp;

    for (size_t i = 0; i < winput.size(); i++) {
        wchar_t wc = winput[i];
        size_t found=wsigns.find(wc);
        if ((found != std::string::npos) ){
            wtemp += L" ";
        }
        else
            wtemp += wc;
    }

    string temp = cv.to_bytes(wtemp);
    string result;
    static const string signs = "!\"#$%&\'()*+,/;<=>?@[\\]^_`{|}~";  //exclude :-.
    for (size_t i = 0; i < temp.size(); i++) {
        size_t found = signs.find(temp[i]);
        if (found  != std::string::npos)
            result += " ";
        else
            result += temp[i];
    }

    return result;
}


string norm(string input){
    static const regex regex_link( "(https?|ftp)://\\S+", std::regex_constants::icase );
    static const regex regex_email( "(https?|ftp)://\\S+", std::regex_constants::icase );

    string temp1 = std::regex_replace( input, regex_link, "JDHTTP");
    string temp2 = std::regex_replace( temp1, regex_email, "JDEMAIL");
    temp1 = Half(temp2);
    temp2 = ReplaceSmileyAndSign(temp1);

    static const regex regex_space("\\s+");
    temp1 = std::regex_replace( temp2, regex_space, " ");

    return temp1;
}



int main()
{   string x = "this中 文A，B ｃｈｉｎａ。 is , http://abder.dofj.sdf/sjodir/ams in text";
    x = "a☹︎b😐";
    cout << x << endl;
    cout << norm(x) << endl;
}


