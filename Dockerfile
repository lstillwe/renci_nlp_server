FROM centos:centos6.7
MAINTAINER Lisa Stillwell <lisa@renci.org>


RUN yum -y update; yum clean all; yum -y install epel-release; yum clean all; yum -y install wget

# Install postgresql and setup database
RUN rpm -Uvh http://yum.postgresql.org/9.4/redhat/rhel-6-x86_64/pgdg-centos94-9.4-3.noarch.rpm
RUN yum -y install postgresql94 postgresql94-server postgresql94-contrib postgresql94-devel; ln -s /usr/pgsql-9.4/bin/pg_config /usr/bin/pg_config; service postgresql-9.4 initdb; sed -i 's/^host[ \t]*all[ \t]*all[ \t]*127\.0\.0\.1\/32[ \t]*ident/host  all  all  127\.0\.0\.1\/32  password/' /var/lib/pgsql/9.4/data/pg_hba.conf

# Install Java 1.8
RUN wget --no-cookies --no-check-certificate --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/8u111-b14/jdk-8u111-linux-x64.tar.gz; tar -xzf jdk-8u111-linux-x64.tar.gz; cd jdk1.8.0_111/;  alternatives --install /usr/bin/java java /jdk1.8.0_111/bin/java 1

# Install Python 2.7 and all prereqs
RUN yum -y install gcc zlib-devel unzip sqlite-devel openssl openssl-devel
RUN wget https://www.python.org/ftp/python/2.7.12/Python-2.7.12.tgz; tar -xzvf Python-2.7.12.tgz; cd Python-2.7.12; ./configure; make; make altinstall
RUN yum -y install python-pip; pip install --upgrade pip; pip install virtualenv requests; virtualenv -p /usr/local/bin/python2.7 renci_nlp_server

# Download and install all NLP code
RUN wget http://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip; unzip stanford-corenlp-full-2015-12-09.zip; rm stanford-corenlp-full-2015-12-09.zip
RUN wget wget https://github.com/brendano/stanford_corenlp_pywrapper/archive/master.zip; unzip master.zip; rm master.zip
RUN wget https://github.com/lstillwe/renci_nlp_server/archive/master.zip; unzip master.zip; cp -r renci_nlp_server-master/* renci_nlp_server; rm master.zip
RUN mv stanford-corenlp-full-2015-12-09 renci_nlp_server/stanford-corenlp; cp renci_nlp_server/stanford-corenlp/stanford-corenlp-full-2015-12-09/*.jar renci_nlp_server/stanford-corenlp; mv stanford_corenlp_pywrapper-master renci_nlp_server/stanford_corenlp_pywrapper; cd renci_nlp_server; source ./bin/activate; cd stanford_corenlp_pywrapper; pip install .; cd ..; pip install -r requirements.txt; python -m nltk.downloader -d /usr/local/share/nltk_data wordnet

#ADD ./start.sh /start.sh
# RUN echo %sudo        ALL=NOPASSWD: ALL >> /etc/sudoers
#EXPOSE 3306

CMD ["/bin/bash", "renci_nlp_server/start.sh"]`
#CMD ["/bin/bash"]`
