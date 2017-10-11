#include <bits/stdc++.h>
#include <thread>
#include <errno.h>
using namespace std;

#define SYSERROR()  errno

string outputFolder = "Merged/";
string inputPath, inputFolder, fileData, secondaryData;
string fields[6] = {"Body/", "Category/", "Infobox/", "Links/", "References/", "Title/"};
int numberOfFiles = 17641;

auto cmp = [](pair<pair<string, string >, int > a, pair<pair<string, string >, int > b){return a.first.first > b.first.first;};
priority_queue<pair<pair<string, string >, int >, vector<pair<pair<string, string >, int > >, decltype(cmp)> pq(cmp);
vector<pair<int, int > > v;
pair<string, string > p, q, r;
pair<pair<string, string >, int > p2, q2;
string word, posting;
ifstream files[17642];

void mergeFiles(string field)
{
    int outputFileCount = 0;
    int numberOfLines = 0;
    fileData = "";
    secondaryData = "";
    //ifstream files[numberOfFiles];
    ofstream secondaryIndexFile, file;
    secondaryIndexFile.open(inputPath + outputFolder + field + "offset.txt");
    string data, prefix = field;
    prefix[0] = char(prefix[0]-'A'+'a');
    prefix.pop_back();

    int cnt=0;
    for(int i=0;i<numberOfFiles;i++)
    {
      string fileName = inputFolder + field + prefix + to_string(i) + ".txt";
      files[i].open(fileName.c_str());
      if((files[i].is_open()))
      {
        cnt++;
      }
      files[i] >> data;
      if(data == "")
        return;
      stringstream ss(data);
      string temp;
      bool first = true;
      while(getline(ss, temp, ':'))
      {
        if(first)
        {
          p.first = temp;
          first = false;
        }
        else
          p.second = temp;
      }
      pq.push(make_pair(p, i));
    }
    cerr << cnt << endl;
    string last;
    while(!pq.empty())
    {
      p2 = pq.top();
      last = p2.first.first;
      pq.pop();
      word = p2.first.first;
      posting = p2.first.second + "|";
      int currentFileNumber = p2.second;

      if(files[currentFileNumber] >> data)
      {
        stringstream ss(data);
        string temp;
        bool first = true;
        while(getline(ss, temp, ':'))
        {
          if(first)
          {
            q.first = temp;
            first = false;
          }
          else
            q.second = temp;
        }
        pq.push(make_pair(q, currentFileNumber));
      }

      if(!pq.empty())
      {
          q2 = pq.top();
          while(!pq.empty() && q2.first.first == p2.first.first)
          {
            posting += q2.first.second + "|";
            pq.pop();

            if(files[q2.second] >> data)
            {
              stringstream ss(data);
              string temp;
              bool first = true;
              while(getline(ss, temp, ':'))
              {
                if(first)
                {
                  r.first = temp;
                  first = false;
                }
                else
                  r.second = temp;
              }
              pq.push(make_pair(r, q2.second));
            }
            q2 = pq.top();
          }
      }

      stringstream ss(posting);
      string temp;
      while(getline(ss, temp, '|'))
      {
        stringstream ss2(temp);
        string temp2;
        pair<int, int > temp3;
        bool first = true;
        while(getline(ss2, temp2, ','))
        {
          if(first)
          {
            temp3.first = stoi(temp2);
            first = false;
          }
          else
            temp3.second = stoi(temp2);
        }
        v.push_back(temp3);
      }
      sort(v.begin(), v.end(), [](pair<int, int > a, pair<int, int > b){
        return a.second > b.second;
      });
      numberOfLines++;

      string finalPosting = "";
      for(int i=0;i<v.size();i++)
      {
        temp = to_string(v[i].first);
        temp += ",";
        temp += to_string(v[i].second);
        temp += "|";
        finalPosting += temp ;
      }
      v.clear();
      if(finalPosting[finalPosting.size()-1] == '|')finalPosting.pop_back();
      finalPosting += "\n";
      fileData += p2.first.first + ":" + finalPosting;

      if(numberOfLines == 2500)
      {
        secondaryData = p2.first.first + "\n";
        secondaryIndexFile << secondaryData;
        secondaryData = "";
        temp = inputPath + outputFolder + field + prefix + to_string(outputFileCount) + ".txt";
        cerr << temp << endl;
        file.open(temp.c_str());
        file << fileData;
        file.close();
        numberOfLines = 0;
        fileData = "";
        outputFileCount++;
      }
    }
    if(!fileData.empty())
    {
      secondaryData = last + "\n";
      secondaryIndexFile << secondaryData;
      string temp = inputPath + outputFolder + field + prefix + to_string(outputFileCount) + ".txt";
      ofstream file(temp);
      file << fileData;
      file.close();
      secondaryData = "";
      numberOfLines = 0;
      fileData = "";
      outputFileCount++;
    }
    for(int i=0;i<numberOfFiles;i++)
      files[i].close();
    secondaryIndexFile.close();
}

int main(int argc, char *argv[])
{
  ios_base::sync_with_stdio(false);
  cin.tie(NULL);
  string temp(argv[1]);
  inputPath = temp;
  inputFolder = inputPath + "Index/";
  bool first = 1;
  ifstream in;
  ofstream out;
  string line;
  temp = inputFolder + "titles.txt";
  string outputFileName = inputPath + outputFolder + "titles.txt";
  /*in.open(temp);
  out.open(outputFileName);
  while(getline(in, line))
  {
      if(first)
      {
        numberOfFiles = stoi(line);
        first = 0;
      }
      line += "\n";
      out << line;
  }
  in.close();
  out.close();*/
  //numberOfFiles = stoi(string(argv[2]));
  for(int i=0;i<6;i++)
    mergeFiles(fields[0]);
  return 0;
}
