FROM ubuntu:latest
MAINTAINER  Your_name "felix141996@gmail.com"
RUN apt-get update -y
RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y software-properties-common build-essential python3.8 python-dev python3-pip git
VOLUME ["/var/www/app/public"]
ADD . /var/www/app/public
COPY . /var/www/app/public
WORKDIR /var/www/app/public
RUN pip3 install -r requirements.txt
ENTRYPOINT ["sh"]
CMD ["init.sh"]
